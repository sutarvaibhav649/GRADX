const express = require('express');
const {
  getDashboard,
  createExam,
  getMyExams,
  getExamById,
  updateExam,
  deleteExam,
  getExamResults,
} = require('../controllers/faculty.controller');
const { protect } = require('../middleware/auth.middleware');
const { authorize } = require('../middleware/role.middleware');
const upload = require('../config/multer');

const router = express.Router();

router.use(protect, authorize('faculty'));

router.get('/dashboard', getDashboard);
router.post(
  '/exams',
  upload.fields([
    { name: 'studentPapers', maxCount: 50 },
    { name: 'modelAnswer', maxCount: 1 },
  ]),
  createExam
);
router.get('/exams', getMyExams);
router.get('/exams/:id', getExamById);
router.put('/exams/:id', updateExam);
router.delete('/exams/:id', deleteExam);
router.get('/exams/:id/results', getExamResults);

module.exports = router;
