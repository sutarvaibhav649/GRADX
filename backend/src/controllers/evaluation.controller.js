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
                studentExtracted: response.data.student_extracted,
                lowConfidence: response.data.low_confidence || false,
                confidenceNote: response.data.confidence_note || null
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

const uploadModelAnswerToFastAPI = async (modelAnswerPath, examId, sections = []) => {
    try {
        if (!fs.existsSync(modelAnswerPath)) {
            console.error(`Model answer file not found: ${modelAnswerPath}`);
            return null;
        }

        const formData = new FormData();
        formData.append('file', fs.createReadStream(modelAnswerPath));
        if (sections.length > 0) {
            formData.append('sections', JSON.stringify(sections));
        }

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
                message: 'Exam already evaluated. To re-evaluate, delete existing results first.'
            });
        }

        exam.status = 'in_progress';
        await exam.save();
        
        // Fix: Use correct path
        const backendRoot = path.resolve(__dirname, '../..');
        
        const examIdStr = exam._id.toString();

        // Build sections array from exam.questions (empty = use FastAPI defaults)
        const examSections = (exam.questions || []).map(q => ({
            name: q.sectionName,
            marks: q.maxMarks
        }));

        // Phase 1.3: Always verify model answer is in FastAPI memory.
        // FastAPI loses in-memory state on restart, so we check before every evaluation.
        if (exam.modelAnswer) {
            let modelInMemory = false;
            try {
                const cfgRes = await axios.get(
                    `${FASTAPI_BASE}/api/evaluation/config?exam_id=${examIdStr}`,
                    { timeout: 5000 }
                );
                modelInMemory = cfgRes.data.configured === true;
            } catch (e) {
                console.log(`FastAPI config check skipped: ${e.message}`);
            }

            if (!modelInMemory) {
                let restored = false;

                // Fast path: restore from pre-extracted JSON saved in MongoDB (no OCR cost)
                const extractedAnswer = exam.modelAnswerExtracted;
                const hasExtracted = extractedAnswer && Object.keys(extractedAnswer).length > 0
                    && Object.values(extractedAnswer).some(v => v);
                if (hasExtracted) {
                    try {
                        await axios.post(
                            `${FASTAPI_BASE}/api/evaluation/restore-model?exam_id=${examIdStr}`,
                            { answer: extractedAnswer, sections: examSections },
                            { timeout: 10000 }
                        );
                        restored = true;
                        console.log(`Model answer restored from MongoDB JSON for exam ${examIdStr}`);
                    } catch (e) {
                        console.log(`JSON restore failed: ${e.message} — falling back to image upload`);
                    }
                }

                // Slow path: re-upload image and run OCR
                if (!restored) {
                    const modelFileName = path.basename(exam.modelAnswer.filePath);
                    const modelAnswerPath = path.join(backendRoot, 'uploads/model-answers', modelFileName);
                    console.log(`Looking for model answer at: ${modelAnswerPath}`);

                    if (fs.existsSync(modelAnswerPath)) {
                        const uploadResult = await uploadModelAnswerToFastAPI(modelAnswerPath, examIdStr, examSections);
                        if (uploadResult?.success) {
                            exam.modelAnswerUploadedToAI = true;
                            if (uploadResult.model_extracted?.Answer) {
                                exam.modelAnswerExtracted = uploadResult.model_extracted.Answer;
                            }
                            await exam.save();
                            console.log(`Model answer uploaded and extracted for exam ${examIdStr}`);
                        } else {
                            console.log(`Failed to upload model answer for exam ${examIdStr} — will use mock scores`);
                        }
                    } else {
                        console.log(`Model answer file not found: ${modelAnswerPath} — will use mock scores`);
                    }
                }
            } else if (!exam.modelAnswerUploadedToAI) {
                exam.modelAnswerUploadedToAI = true;
                await exam.save();
            }
        }

        // Look up registered students by email (not by department — department filter was too narrow)
        const emailList = exam.studentAnswerSheets.map(s => s.email);
        const students = await User.find({ role: 'student', email: { $in: emailList } });
        const studentByEmail = new Map(students.map(s => [s.email, s]));

        const evaluations = [];
        const skippedStudents = []; // track emails not found in DB

        // Phase 2.3: Resume support — skip students already saved in a previous (failed) run
        const existingResults = await EvaluationResult.find({ examId: exam._id }).select('studentId');
        const alreadyEvaluatedIds = new Set(existingResults.map(r => r.studentId.toString()));
        if (alreadyEvaluatedIds.size > 0) {
            console.log(`Resuming evaluation — ${alreadyEvaluatedIds.size} student(s) already done, skipping them`);
        }

        // Phase 2.1: Process students in parallel batches of 3 for ~3x speed improvement.
        const BATCH_SIZE = 3;
        const sheets = exam.studentAnswerSheets;

        const evaluateStudent = async (sheet) => {
            const student = studentByEmail.get(sheet.email);
            if (!student) {
                console.log(`Student not registered: ${sheet.email} — skipping`);
                return { skipped: true, email: sheet.email };
            }

            // Phase 2.3: skip if this student was already evaluated in a prior run
            if (alreadyEvaluatedIds.has(student._id.toString())) {
                console.log(`  Already evaluated: ${student.email} — skipping (resume)`);
                return { skipped: false, alreadyDone: true };
            }

            const studentFileName = path.basename(sheet.filePath);
            const studentImagePath = path.join(backendRoot, 'uploads/student-papers', studentFileName);
            console.log(`Evaluating ${student.email}`);

            let finalScore, percentage, detailedEval;
            let extractedAnswerData = null;
            let usedMock = false;
            let lowConfidence = false;

            try {
                if (fs.existsSync(studentImagePath)) {
                    const aiResult = await callFastAPIEvaluation(studentImagePath, examIdStr);

                    if (aiResult && aiResult.success) {
                        percentage = parseFloat(aiResult.percentage.toFixed(2));
                        finalScore = Math.round((percentage / 100) * exam.maxMarks);
                        detailedEval = aiResult.detailedResult;
                        extractedAnswerData = aiResult.studentExtracted?.Answer || null;
                        lowConfidence = aiResult.lowConfidence || false;
                        if (detailedEval) {
                            detailedEval.low_confidence = lowConfidence;
                            detailedEval.confidence_note = aiResult.confidenceNote || null;
                        }
                        console.log(`  AI result: ${finalScore}/${exam.maxMarks} (${percentage}%)${lowConfidence ? ' [LOW CONFIDENCE]' : ''}`);
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
                usedMock = true;
                finalScore = simulateAIEvaluation(exam.maxMarks, exam.evaluationStrictness);
                percentage = parseFloat(((finalScore / exam.maxMarks) * 100).toFixed(2));
                console.error(`  Error evaluating ${student.email}:`, studentError.message, '— falling back to mock');
            }

            return {
                skipped: false,
                alreadyDone: false,
                evaluation: {
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
                    extractedAnswer: extractedAnswerData || {},
                    usedMockEvaluation: usedMock
                }
            };
        };

        for (let i = 0; i < sheets.length; i += BATCH_SIZE) {
            const batch = sheets.slice(i, i + BATCH_SIZE);
            const batchResults = await Promise.all(batch.map(evaluateStudent));
            for (const r of batchResults) {
                if (r.skipped) skippedStudents.push(r.email);
                else if (!r.alreadyDone) evaluations.push(r.evaluation);
            }
        }

        // Phase 2.3: Save individually so a single DB error doesn't lose all results
        const insertedResults = [];
        const saveFailures = [];
        for (const ev of evaluations) {
            try {
                const saved = await EvaluationResult.create(ev);
                insertedResults.push(saved);
            } catch (saveErr) {
                console.error(`Failed to save result for student ${ev.studentId}: ${saveErr.message}`);
                saveFailures.push(ev.studentAnswerSheet?.email || String(ev.studentId));
            }
        }

        // Count total evaluated (new + already-done from previous run)
        const totalEvaluated = insertedResults.length + alreadyEvaluatedIds.size;
        exam.status = 'completed';
        exam.evaluatedCount = totalEvaluated;
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
        const lowConfCount = evaluations.filter(e => e.aiEvaluationDetails?.low_confidence).length;
        if (lowConfCount > 0) {
            warnings.push(`${lowConfCount} paper(s) flagged for low OCR confidence — review in cross-check`);
        }
        if (saveFailures.length > 0) {
            warnings.push(`${saveFailures.length} result(s) failed to save: ${saveFailures.join(', ')}`);
        }
        if (alreadyEvaluatedIds.size > 0) {
            warnings.push(`${alreadyEvaluatedIds.size} student(s) were already evaluated and skipped (resume)`);
        }

        res.status(200).json({
            success: true,
            message: `Evaluation completed for ${insertedResults.length} student(s)`,
            warnings: warnings.length > 0 ? warnings : undefined,
            data: {
                examId: exam._id,
                evaluatedCount: totalEvaluated,
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