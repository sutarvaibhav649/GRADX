const express = require('express');
const { 
    startEvaluation, 
    uploadModelAnswerToAI,
    getExamEvaluations, 
    updateEvaluationResult, 
    finalizeResult, 
    getResultById 
} = require('../controllers/evaluation.controller');
const { protect } = require('../middleware/auth.middleware');
const { authorize } = require('../middleware/role.middleware');

const router = express.Router();

// All routes require authentication
router.use(protect);

// Faculty-only routes
router.post('/start/:examId', authorize('faculty'), startEvaluation);
router.post('/upload-model/:examId', authorize('faculty'), uploadModelAnswerToAI);
router.get('/exam/:examId', authorize('faculty', 'admin'), getExamEvaluations);
router.put('/results/:id', authorize('faculty'), updateEvaluationResult);
router.put('/results/:id/finalize', authorize('faculty'), finalizeResult);

// Any authenticated user can view results (ownership enforced in controller)
router.get('/results/:id', getResultById);

module.exports = router;