const EvaluationResult = require('../models/EvaluationResult');
const Exam = require('../models/Exam');

// GET /api/student/dashboard
const getDashboard = async (req, res) => {
  try {
    const results = await EvaluationResult.find({ studentId: req.user._id })
      .populate('examId', 'subject examType department academicYear maxMarks semester year')
      .sort({ createdAt: -1 });

    const finalized = results.filter((r) => r.evaluationStatus === 'finalized');
    const avgScore =
      finalized.length > 0
        ? (finalized.reduce((sum, r) => sum + r.percentage, 0) / finalized.length).toFixed(2)
        : 0;
    const topPerformances = finalized.filter((r) => r.percentage >= 75).length;

    const recentResults = results.slice(0, 5);

    res.status(200).json({
      success: true,
      data: {
        stats: {
          totalEvaluated: finalized.length,
          averageScore: parseFloat(avgScore),
          topPerformances,
          pendingResults: results.filter((r) => r.evaluationStatus === 'pending').length,
        },
        recentResults,
      },
    });
  } catch (error) {
    res.status(500).json({ success: false, message: error.message });
  }
};

// GET /api/student/results
const getMyResults = async (req, res) => {
  try {
    const { examType, department, page = 1, limit = 10 } = req.query;
    const skip = (parseInt(page) - 1) * parseInt(limit);

    const examFilter = {};
    if (examType) examFilter.examType = examType;
    if (department) examFilter.department = department;

    const examIds = Object.keys(examFilter).length
      ? (await Exam.find(examFilter).select('_id')).map((e) => e._id)
      : null;

    const filter = { studentId: req.user._id };
    if (examIds) filter.examId = { $in: examIds };

    const [results, total] = await Promise.all([
      EvaluationResult.find(filter)
        .populate('examId', 'subject examType department academicYear maxMarks semester year facultyId')
        .skip(skip)
        .limit(parseInt(limit))
        .sort({ createdAt: -1 }),
      EvaluationResult.countDocuments(filter),
    ]);

    res.status(200).json({
      success: true,
      data: results,
      pagination: { total, page: parseInt(page), limit: parseInt(limit), pages: Math.ceil(total / limit) },
    });
  } catch (error) {
    res.status(500).json({ success: false, message: error.message });
  }
};

// GET /api/student/results/:id
const getResultById = async (req, res) => {
  try {
    const result = await EvaluationResult.findOne({
      _id: req.params.id,
      studentId: req.user._id,
    }).populate('examId', 'subject examType department academicYear maxMarks semester year evaluationMode');

    if (!result) return res.status(404).json({ success: false, message: 'Result not found' });

    res.status(200).json({ success: true, data: result });
  } catch (error) {
    res.status(500).json({ success: false, message: error.message });
  }
};

module.exports = { getDashboard, getMyResults, getResultById };
