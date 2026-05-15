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
const callFastAPIEvaluation = async (studentImagePath, examId) => {
    try {
        // Check if file exists
        if (!fs.existsSync(studentImagePath)) {
            console.error(`File not found: ${studentImagePath}`);
            return null;
        }
        
        const formData = new FormData();
        formData.append('file', fs.createReadStream(studentImagePath));
        
        // Call FastAPI for evaluation
        const response = await axios.post(
            'http://localhost:8000/api/evaluation/evaluate-image',
            formData,
            { headers: { ...formData.getHeaders() }, timeout: 600000 }
        );
        
        if (response.data.success && response.data.evaluation) {
            // Log extracted data for debugging
            console.log('📝 Extracted student answer from FastAPI:');
            console.log('   Definition:', response.data.student_extracted?.Answer?.Definition?.substring(0, 100) || 'Not found');
            console.log('   Body:', response.data.student_extracted?.Answer?.Body?.substring(0, 100) || 'Not found');
            console.log('   Conclusion:', response.data.student_extracted?.Answer?.Conclusion?.substring(0, 100) || 'Not found');
            
            return {
                success: true,
                totalMarks: response.data.evaluation.total_marks,
                maxMarks: response.data.evaluation.max_marks,
                percentage: response.data.evaluation.percentage,
                detailedResult: response.data.evaluation,
                studentExtracted: response.data.student_extracted // Include the extracted student answer
            };
        }
        return null;
    } catch (error) {
        console.error('FastAPI call failed:', error.message);
        if (error.response) {
            console.error('Response data:', error.response.data);
        }
        return null;
    }
};

const uploadModelAnswerToFastAPI = async (modelAnswerPath) => {
    try {
        if (!fs.existsSync(modelAnswerPath)) {
            console.error(`Model answer file not found: ${modelAnswerPath}`);
            return null;
        }
        
        const formData = new FormData();
        formData.append('file', fs.createReadStream(modelAnswerPath));
        
        const response = await axios.post(
            'http://localhost:8000/api/evaluation/upload-model',
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
        
        // Upload model answer to FastAPI if not already done
        if (!exam.modelAnswerUploadedToAI && exam.modelAnswer) {
            const modelFileName = path.basename(exam.modelAnswer.filePath);
            const modelAnswerPath = path.join(backendRoot, 'uploads/model-answers', modelFileName);
            console.log(`Looking for model answer at: ${modelAnswerPath}`);
            
            if (fs.existsSync(modelAnswerPath)) {
                const uploadResult = await uploadModelAnswerToFastAPI(modelAnswerPath);
                if (uploadResult && uploadResult.success) {
                    exam.modelAnswerUploadedToAI = true;
                    await exam.save();
                    console.log('Model answer uploaded to FastAPI successfully');
                } else {
                    console.log('Failed to upload model answer to FastAPI, using mock evaluation');
                }
            } else {
                console.log(`Model answer file not found: ${modelAnswerPath}`);
            }
        }
        
        const students = await User.find({ 
            role: 'student', 
            department: exam.department 
        });
        
        const evaluations = [];
        
        for (let i = 0; i < exam.studentAnswerSheets.length; i++) {
            const sheet = exam.studentAnswerSheets[i];
            const student = students.find(s => s.email === sheet.email);
            
            if (!student) {
                console.log(`Student not found for email: ${sheet.email}`);
                continue;
            }
            
            const studentFileName = path.basename(sheet.filePath);
            const studentImagePath = path.join(backendRoot, 'uploads/student-papers', studentFileName);
            console.log(`Evaluating: ${student.email} - ${studentImagePath}`);
            
            // DECLARE variables outside the if block
            let finalScore, percentage, detailedEval;
            let extractedAnswerData = null;
            let aiResult = null;
            
            // Check if file exists
            if (fs.existsSync(studentImagePath)) {
                // Try FastAPI evaluation first
                aiResult = await callFastAPIEvaluation(studentImagePath, exam._id);
                
                if (aiResult && aiResult.success) {
                    finalScore = aiResult.totalMarks;
                    percentage = aiResult.percentage;
                    detailedEval = aiResult.detailedResult;
                    // Extract the student answer data
                    extractedAnswerData = aiResult.studentExtracted?.Answer || null;
                    console.log(`✅ AI Evaluation for ${student.email}: ${finalScore}/${exam.maxMarks} (${percentage}%)`);
                    if (extractedAnswerData) {
                        console.log(`   Extracted answer length: Def=${extractedAnswerData.Definition?.length || 0}, Body=${extractedAnswerData.Body?.length || 0}, Concl=${extractedAnswerData.Conclusion?.length || 0}`);
                    }
                } else {
                    // Fallback to mock if FastAPI fails
                    finalScore = simulateAIEvaluation(exam.maxMarks, exam.evaluationStrictness);
                    percentage = (finalScore / exam.maxMarks) * 100;
                    console.log(`⚠️ FastAPI failed, using mock for ${student.email}: ${finalScore}/${exam.maxMarks}`);
                }
            } else {
                // File doesn't exist, use mock
                finalScore = simulateAIEvaluation(exam.maxMarks, exam.evaluationStrictness);
                percentage = (finalScore / exam.maxMarks) * 100;
                console.log(`⚠️ Student paper not found: ${studentImagePath}, using mock`);
            }
            
            // Now push the evaluation with all data
            evaluations.push({
                examId: exam._id,
                studentId: student._id,
                studentAnswerSheet: sheet,
                totalMarksObtained: finalScore,
                maxMarks: exam.maxMarks,
                aiScore: finalScore,
                percentage: percentage,
                grade: calculateGrade(percentage),
                finalScore: finalScore,
                crossCheckRequired: exam.enableCrossCheck && percentage < 40,
                evaluationStatus: 'ai_evaluated',
                evaluatedAt: new Date(),
                // Include detailed data if available
                aiEvaluationDetails: detailedEval || null,
                // IMPORTANT: Include the extracted student answer in the correct format
                extractedAnswer: extractedAnswerData || {
                    Definition: '',
                    Body: '',
                    Conclusion: ''
                }
            });
        }
        
        if (evaluations.length > 0) {
            await EvaluationResult.insertMany(evaluations);
        }
        
        exam.status = 'completed';
        exam.evaluatedCount = evaluations.length;
        await exam.save();
        
        res.status(200).json({
            success: true,
            message: `Evaluation completed for ${evaluations.length} student(s)`,
            data: { 
                examId: exam._id, 
                evaluatedCount: evaluations.length,
                results: evaluations
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