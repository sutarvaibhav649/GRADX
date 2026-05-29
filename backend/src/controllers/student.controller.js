const EvaluationResult = require('../models/EvaluationResult');
const Exam = require('../models/Exam');

// GET /api/student/dashboard
const getDashboard = async (req, res) => {
  try {
    const results = await EvaluationResult.find({ studentId: req.user._id })
      .populate('examId', 'subject examType department academicYear maxMarks semester year')
      .sort({ createdAt: -1 });

    const evaluated = results.filter((r) => r.evaluationStatus !== 'pending');
    const avgScore =
      evaluated.length > 0
        ? (evaluated.reduce((sum, r) => sum + (Number(r.percentage) || 0), 0) / evaluated.length).toFixed(2)
        : 0;
    const topPerformances = evaluated.filter((r) => (Number(r.percentage) || 0) >= 75).length;

    const recentResults = evaluated.slice(0, 5);

    res.status(200).json({
      success: true,
      data: {
        stats: {
          totalEvaluated: evaluated.length,
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

    const filter = { studentId: req.user._id, evaluationStatus: { $ne: 'pending' } };
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
    if (!result.examId) return res.status(404).json({ success: false, message: 'Exam details not found for this result' });

    // Class stats: avg, rank, total students evaluated in the same exam
    const classResults = await EvaluationResult.find({
      examId: result.examId._id,
      evaluationStatus: { $ne: 'pending' },
    }).select('finalScore percentage studentId');

    const classPercentages = classResults
      .map((r) => Number(r.percentage))
      .filter((percentage) => !Number.isNaN(percentage));
    const classAvg =
      classPercentages.length > 0
        ? parseFloat(
            (classPercentages.reduce((sum, percentage) => sum + percentage, 0) / classPercentages.length).toFixed(2)
          )
        : 0;

    const resultPercentage = Number(result.percentage) || 0;
    const rank =
      classResults.filter(
        (r) =>
          (Number(r.percentage) || 0) > resultPercentage &&
          r.studentId.toString() !== req.user._id.toString()
      ).length + 1;

    res.status(200).json({
      success: true,
      data: {
        ...result.toObject(),
        classStats: {
          totalStudents: classResults.length,
          classAverage: classAvg,
          rank,
        },
      },
    });
  } catch (error) {
    res.status(500).json({ success: false, message: error.message });
  }
};

module.exports = { getDashboard, getMyResults, getResultById };
