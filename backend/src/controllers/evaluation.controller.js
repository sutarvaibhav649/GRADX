const Exam = require('../models/Exam');
const EvaluationResult = require('../models/EvaluationResult');
const User = require('../models/User');
const path = require('path');
const axios = require('axios');
const FormData = require('form-data');
const fs = require('fs');

// ==================== HELPER FUNCTIONS ====================
function calculateGrade(percentage) {
    if (percentage >= 90) return 'O';
    if (percentage >= 80) return 'A+';
    if (percentage >= 70) return 'A';
    if (percentage >= 60) return 'B+';
    if (percentage >= 50) return 'B';
    if (percentage >= 40) return 'C';
    return 'F';
}

// Mock evaluation function (fallback when FastAPI is unavailable)
function simulateAIEvaluation(maxMarks, strictness) {
    const strictnessMultiplier = { lenient: 0.85, moderate: 0.72, strict: 0.60 };
    const base = strictnessMultiplier[strictness] || 0.72;
    const variance = 0.2;
    const rawScore = base + (Math.random() * variance * 2 - variance);
    const clampedScore = Math.max(0.3, Math.min(1.0, rawScore));
    return Math.round(clampedScore * maxMarks);
}

// ==================== FASTAPI INTEGRATION ====================
const FASTAPI_BASE = process.env.FASTAPI_URL || 'http://localhost:8000';

const callFastAPIEvaluation = async (studentImagePath, examId) => {
    try {
        if (!fs.existsSync(studentImagePath)) {
            console.error(`File not found: ${studentImagePath}`);
            return null;
        }

        const formData = new FormData();
        formData.append('file', fs.createReadStream(studentImagePath));

        const response = await axios.post(
            `${FASTAPI_BASE}/api/evaluation/evaluate-image?exam_id=${examId}`,
            formData,
            { headers: { ...formData.getHeaders() }, timeout: 600000 }
        );

        if (response.data.success && response.data.evaluation) {
            return {
                success: true,
                totalMarks: response.data.evaluation.total_marks,
                maxMarks: response.data.evaluation.max_marks,
                percentage: response.data.evaluation.percentage,
                detailedResult: response.data.evaluation,
                studentExtracted: response.data.student_extracted
            };
        }
        return null;
    } catch (error) {
        console.error('FastAPI evaluation call failed:', error.message);
        if (error.response) {
            console.error('FastAPI response:', error.response.data);
        }
        return null;
    }
};

const uploadModelAnswerToFastAPI = async (modelAnswerPath, examId) => {
    try {
        if (!fs.existsSync(modelAnswerPath)) {
            console.error(`Model answer file not found: ${modelAnswerPath}`);
            return null;
        }

        const formData = new FormData();
        formData.append('file', fs.createReadStream(modelAnswerPath));

        const response = await axios.post(
            `${FASTAPI_BASE}/api/evaluation/upload-model?exam_id=${examId}`,
            formData,
            { headers: { ...formData.getHeaders() }, timeout: 60000 }
        );

        return response.data;
    } catch (error) {
        console.error('Failed to upload model answer to FastAPI:', error.message);
        return null;
    }
};

// ==================== CONTROLLER FUNCTIONS ====================
const uploadModelAnswerToAI = async (req, res) => {
    try {
        const exam = await Exam.findOne({ 
            _id: req.params.examId, 
            facultyId: req.user._id 
        });
        
        if (!exam) {
            return res.status(404).json({ 
                success: false, 
                message: 'Exam not found' 
            });
        }
        
        exam.modelAnswerUploadedToAI = true;
        await exam.save();
        
        res.status(200).json({
            success: true,
            message: 'Model answer prepared for AI evaluation'
        });
    } catch (error) {
        console.error('Upload model error:', error);
        res.status(500).json({ 
            success: false, 
            message: error.message 
        });
    }
};

const startEvaluation = async (req, res) => {
    let exam = null;
    try {
        exam = await Exam.findOne({ 
            _id: req.params.examId, 
            facultyId: req.user._id 
        });
        
        if (!exam) {
            return res.status(404).json({ 
                success: false, 
                message: 'Exam not found' 
            });
        }
        
        if (exam.status === 'completed') {
            return res.status(400).json({ 
                success: false, 
                message: 'Exam already evaluated' 
            });
        }
        
        exam.status = 'in_progress';
        await exam.save();
        
        // Fix: Use correct path
        const backendRoot = path.resolve(__dirname, '../..');
        
        const examIdStr = exam._id.toString();

        // Upload model answer to FastAPI (scoped by examId so concurrent exams don't conflict)
        if (!exam.modelAnswerUploadedToAI && exam.modelAnswer) {
            const modelFileName = path.basename(exam.modelAnswer.filePath);
            const modelAnswerPath = path.join(backendRoot, 'uploads/model-answers', modelFileName);
            console.log(`Looking for model answer at: ${modelAnswerPath}`);

            if (fs.existsSync(modelAnswerPath)) {
                const uploadResult = await uploadModelAnswerToFastAPI(modelAnswerPath, examIdStr);
                if (uploadResult && uploadResult.success) {
                    exam.modelAnswerUploadedToAI = true;
                    await exam.save();
                    console.log(`Model answer uploaded to FastAPI for exam ${examIdStr}`);
                } else {
                    console.log(`Failed to upload model answer to FastAPI for exam ${examIdStr} — will use mock scores`);
                }
            } else {
                console.log(`Model answer file not found: ${modelAnswerPath} — will use mock scores`);
            }
        }

        // Look up registered students by email (not by department — department filter was too narrow)
        const emailList = exam.studentAnswerSheets.map(s => s.email);
        const students = await User.find({ role: 'student', email: { $in: emailList } });
        const studentByEmail = new Map(students.map(s => [s.email, s]));

        const evaluations = [];
        const skippedStudents = []; // track emails not found in DB

        for (let i = 0; i < exam.studentAnswerSheets.length; i++) {
            const sheet = exam.studentAnswerSheets[i];
            const student = studentByEmail.get(sheet.email);

            if (!student) {
                console.log(`Student not registered: ${sheet.email} — skipping`);
                skippedStudents.push(sheet.email);
                continue;
            }

            const studentFileName = path.basename(sheet.filePath);
            const studentImagePath = path.join(backendRoot, 'uploads/student-papers', studentFileName);
            console.log(`Evaluating ${student.email}`);

            let finalScore, percentage, detailedEval;
            let extractedAnswerData = null;
            let usedMock = false;

            try {
                if (fs.existsSync(studentImagePath)) {
                    const aiResult = await callFastAPIEvaluation(studentImagePath, examIdStr);

                    if (aiResult && aiResult.success) {
                        // Scale FastAPI percentage to exam.maxMarks
                        percentage = parseFloat(aiResult.percentage.toFixed(2));
                        finalScore = Math.round((percentage / 100) * exam.maxMarks);
                        detailedEval = aiResult.detailedResult;
                        extractedAnswerData = aiResult.studentExtracted?.Answer || null;
                        console.log(`  AI result: ${finalScore}/${exam.maxMarks} (${percentage}%)`);
                    } else {
                        usedMock = true;
                        finalScore = simulateAIEvaluation(exam.maxMarks, exam.evaluationStrictness);
                        percentage = parseFloat(((finalScore / exam.maxMarks) * 100).toFixed(2));
                        console.log(`  FastAPI returned no result — mock: ${finalScore}/${exam.maxMarks}`);
                    }
                } else {
                    usedMock = true;
                    finalScore = simulateAIEvaluation(exam.maxMarks, exam.evaluationStrictness);
                    percentage = parseFloat(((finalScore / exam.maxMarks) * 100).toFixed(2));
                    console.log(`  Image not found — mock: ${finalScore}/${exam.maxMarks}`);
                }
            } catch (studentError) {
                // Isolate: one student's failure must not abort the entire evaluation
                usedMock = true;
                finalScore = simulateAIEvaluation(exam.maxMarks, exam.evaluationStrictness);
                percentage = parseFloat(((finalScore / exam.maxMarks) * 100).toFixed(2));
                console.error(`  Error evaluating ${student.email}:`, studentError.message, '— falling back to mock');
            }

            evaluations.push({
                examId: exam._id,
                studentId: student._id,
                studentAnswerSheet: sheet,
                totalMarksObtained: finalScore,
                maxMarks: exam.maxMarks,
                aiScore: finalScore,
                percentage,
                grade: calculateGrade(percentage),
                finalScore,
                crossCheckRequired: exam.enableCrossCheck,
                evaluationStatus: 'ai_evaluated',
                evaluatedAt: new Date(),
                aiEvaluationDetails: detailedEval || null,
                extractedAnswer: extractedAnswerData || { Definition: '', Body: '', Conclusion: '' },
                usedMockEvaluation: usedMock
            });
        }

        let insertedResults = [];
        if (evaluations.length > 0) {
            insertedResults = await EvaluationResult.insertMany(evaluations);
        }

        exam.status = 'completed';
        exam.evaluatedCount = insertedResults.length;
        await exam.save();

        // Merge MongoDB _id back so the frontend cross-check modal can call PUT /results/:id
        const resultsWithIds = evaluations.map((ev, idx) => ({
            ...ev,
            _id: insertedResults[idx]?._id
        }));

        const warnings = [];
        if (skippedStudents.length > 0) {
            warnings.push(`${skippedStudents.length} student(s) not registered in the system and were skipped: ${skippedStudents.join(', ')}`);
        }
        const mockCount = evaluations.filter(e => e.usedMockEvaluation).length;
        if (mockCount > 0) {
            warnings.push(`${mockCount} student paper(s) used mock scores (AI unavailable or file missing)`);
        }

        res.status(200).json({
            success: true,
            message: `Evaluation completed for ${insertedResults.length} student(s)`,
            warnings: warnings.length > 0 ? warnings : undefined,
            data: {
                examId: exam._id,
                evaluatedCount: insertedResults.length,
                skippedStudents,
                results: resultsWithIds
            }
        });
        
    } catch (error) {
        console.error('Evaluation error:', error);
        if (exam) {
            try {
                exam.status = 'pending';
                await exam.save();
            } catch (saveError) {
                console.error('Error saving exam status:', saveError);
            }
        }
        res.status(500).json({ 
            success: false, 
            message: error.message 
        });
    }
};

const getExamEvaluations = async (req, res) => {
    try {
        const exam = await Exam.findOne({ 
            _id: req.params.examId, 
            facultyId: req.user._id 
        });
        
        if (!exam) {
            return res.status(403).json({ 
                success: false, 
                message: 'Not authorized to view this exam' 
            });
        }
        
        const results = await EvaluationResult.find({ examId: exam._id })
            .populate('studentId', 'fullName idNumber department email');
        
        res.status(200).json({ success: true, data: results });
    } catch (error) {
        console.error('Get exam evaluations error:', error);
        res.status(500).json({ 
            success: false, 
            message: error.message 
        });
    }
};

const updateEvaluationResult = async (req, res) => {
    try {
        const { questionWiseMarks, manualAdjustment, crossCheckNotes, crossCheckCompleted } = req.body;
        const result = await EvaluationResult.findById(req.params.id).populate('examId');
        
        if (!result) {
            return res.status(404).json({ 
                success: false, 
                message: 'Evaluation result not found' 
            });
        }
        
        if (result.examId.facultyId.toString() !== req.user._id.toString()) {
            return res.status(403).json({ 
                success: false, 
                message: 'Not authorized to edit this result' 
            });
        }
        
        if (questionWiseMarks && Array.isArray(questionWiseMarks)) {
            result.questionWiseMarks = questionWiseMarks;
            result.totalMarksObtained = questionWiseMarks.reduce((sum, q) => sum + q.marksObtained, 0);
            result.finalScore = result.totalMarksObtained;
        }
        
        if (manualAdjustment !== undefined) {
            result.manualAdjustment = manualAdjustment;
            result.finalScore = Math.max(0, Math.min(result.maxMarks, result.totalMarksObtained + manualAdjustment));
        }
        
        if (crossCheckNotes !== undefined) result.crossCheckNotes = crossCheckNotes;
        if (crossCheckCompleted !== undefined) result.crossCheckCompleted = crossCheckCompleted;
        
        result.evaluationStatus = 'manually_reviewed';
        result.reviewedBy = req.user._id;
        result.reviewedAt = new Date();
        
        await result.save();
        res.status(200).json({ success: true, data: result });
    } catch (error) {
        console.error('Update evaluation error:', error);
        res.status(500).json({ 
            success: false, 
            message: error.message 
        });
    }
};

const finalizeResult = async (req, res) => {
    try {
        const results = await EvaluationResult.find({ examId: req.params.id }).populate('examId');
        
        if (!results.length) {
            return res.status(404).json({ 
                success: false, 
                message: 'Results not found' 
            });
        }
        
        for (const result of results) {
            if (result.examId.facultyId.toString() !== req.user._id.toString()) {
                return res.status(403).json({ 
                    success: false, 
                    message: 'Not authorized to finalize this result' 
                });
            }
            if (result.evaluationStatus !== 'finalized') {
                result.evaluationStatus = 'finalized';
                await result.save();
            }
        }
        
        res.status(200).json({ 
            success: true, 
            message: 'Results finalized' 
        });
    } catch (error) {
        console.error('Finalize result error:', error);
        res.status(500).json({ 
            success: false, 
            message: error.message 
        });
    }
};

const getResultById = async (req, res) => {
    try {
        const result = await EvaluationResult.findById(req.params.id)
            .populate('examId')
            .populate('studentId')
            .populate('reviewedBy');
        
        if (!result) {
            return res.status(404).json({ 
                success: false, 
                message: 'Result not found' 
            });
        }
        
        // Check authorization
        if (result.examId.facultyId.toString() !== req.user._id.toString() &&
            result.studentId._id.toString() !== req.user._id.toString() &&
            req.user.role !== 'admin') {
            return res.status(403).json({ 
                success: false, 
                message: 'Not authorized to view this result' 
            });
        }
        
        res.status(200).json({ success: true, data: result });
    } catch (error) {
        console.error('Get result by ID error:', error);
        res.status(500).json({ 
            success: false, 
            message: error.message 
        });
    }
};

// ==================== EXPORTS ====================
module.exports = {
    startEvaluation,
    uploadModelAnswerToAI,
    getExamEvaluations,
    updateEvaluationResult,
    finalizeResult,
    getResultById
};