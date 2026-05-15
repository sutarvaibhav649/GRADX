const express = require('express');
const { getDashboard, getMyResults, getResultById } = require('../controllers/student.controller');
const { protect } = require('../middleware/auth.middleware');
const { authorize } = require('../middleware/role.middleware');

const router = express.Router();

router.use(protect, authorize('student'));

router.get('/dashboard', getDashboard);
router.get('/results', getMyResults);
router.get('/results/:id', getResultById);

module.exports = router;
