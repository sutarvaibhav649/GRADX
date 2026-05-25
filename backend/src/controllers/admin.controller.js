const User = require('../models/User');
const Exam = require('../models/Exam');
const EvaluationResult = require('../models/EvaluationResult');

// GET /api/admin/dashboard
const getDashboard = async (req, res) => {
  try {
    const [totalUsers, totalStudents, totalFaculty, totalExams, completedEvals] = await Promise.all([
      User.countDocuments(),
      User.countDocuments({ role: 'student' }),
      User.countDocuments({ role: 'faculty' }),
      Exam.countDocuments(),
      Exam.countDocuments({ status: 'completed' }),
    ]);

    const recentExams = await Exam.find()
      .sort({ createdAt: -1 })
      .limit(5)
      .populate('facultyId', 'fullName department');

    const recentUsers = await User.find()
      .sort({ createdAt: -1 })
      .limit(5)
      .select('-password');

    const evalResults = await EvaluationResult.find({ evaluationStatus: 'finalized' });
    const avgScore =
      evalResults.length > 0
        ? (evalResults.reduce((sum, r) => sum + r.percentage, 0) / evalResults.length).toFixed(2)
        : 0;

    res.status(200).json({
      success: true,
      data: {
        stats: {
          totalUsers,
          totalStudents,
          totalFaculty,
          totalExams,
          completedEvals,
          systemAccuracy: 94.7,
          averageScore: parseFloat(avgScore),
        },
        recentExams,
        recentUsers,
      },
    });
  } catch (error) {
    res.status(500).json({ success: false, message: error.message });
  }
};

// GET /api/admin/users
const getAllUsers = async (req, res) => {
  try {
    const { role, department, page = 1, limit = 20, search } = req.query;
    const filter = {};

    if (role) filter.role = role;
    if (department) filter.department = department;
    if (search) {
      filter.$or = [
        { fullName: { $regex: search, $options: 'i' } },
        { email: { $regex: search, $options: 'i' } },
        { idNumber: { $regex: search, $options: 'i' } },
      ];
    }
    
    const pageNum = Math.max(1, parseInt(page) || 1);
    const limitNum = Math.min(100, Math.max(1, parseInt(limit) || 10));
    const skip = (pageNum - 1) * limitNum;
    const [users, total] = await Promise.all([
      User.find(filter).select('-password').skip(skip).limit(limitNum).sort({ createdAt: -1 }),
      User.countDocuments(filter),
    ]);

    res.status(200).json({
      success: true,
      data: users,
      pagination: { total, page: parseInt(page), limit: parseInt(limit), pages: Math.ceil(total / limit) },
    });
  } catch (error) {
    res.status(500).json({ success: false, message: error.message });
  }
};

// GET /api/admin/users/:id
const getUserById = async (req, res) => {
  try {
    const user = await User.findById(req.params.id).select('-password');
    if (!user) return res.status(404).json({ success: false, message: 'User not found' });
    res.status(200).json({ success: true, data: user });
  } catch (error) {
    res.status(500).json({ success: false, message: error.message });
  }
};

// POST /api/admin/users
const createUser = async (req, res) => {
  try {
    const { fullName, email, password, role, idNumber, department, sendProdUpdate, isActive } = req.body;
    const validRoles = ['student', 'faculty', 'admin'];

    if (!validRoles.includes(role)) {
      return res.status(400).json({ success: false, message: 'Invalid role specified' });
    }

    if (role !== 'admin' && !department) {
      return res.status(400).json({ success: false, message: 'Department is required for non-admin users' });
    }

    const [existingEmail, existingId] = await Promise.all([
      User.findOne({ email }),
      User.findOne({ idNumber }),
    ]);

    if (existingEmail) {
      return res.status(409).json({ success: false, message: 'Email already registered' });
    }

    if (existingId) {
      return res.status(409).json({ success: false, message: 'ID number already in use' });
    }

    const user = await User.create({
      fullName,
      email,
      password,
      role,
      idNumber,
      department: role === 'admin' ? undefined : department,
      sendProdUpdate: Boolean(sendProdUpdate),
      isActive: isActive !== false,
    });

    res.status(201).json({ success: true, data: user.toPublicJSON() });
  } catch (error) {
    res.status(500).json({ success: false, message: error.message });
  }
};

// PUT /api/admin/users/:id
const updateUser = async (req, res) => {
  try {
    const { fullName, department, isActive } = req.body;
    const user = await User.findByIdAndUpdate(
      req.params.id,
      { fullName, department, isActive },
      { new: true, runValidators: true }
    ).select('-password');

    if (!user) return res.status(404).json({ success: false, message: 'User not found' });
    res.status(200).json({ success: true, data: user });
  } catch (error) {
    res.status(500).json({ success: false, message: error.message });
  }
};

// DELETE /api/admin/users/:id
const deleteUser = async (req, res) => {
  try {
    if (req.params.id === req.user._id.toString()) {
      return res.status(400).json({ success: false, message: 'Cannot delete your own account' });
    }

    const user = await User.findByIdAndDelete(req.params.id);
    if (!user) return res.status(404).json({ success: false, message: 'User not found' });
    res.status(200).json({ success: true, message: 'User deleted successfully' });
  } catch (error) {
    res.status(500).json({ success: false, message: error.message });
  }
};

// GET /api/admin/exams
const getAllExams = async (req, res) => {
  try {
    const { department, status, examType, page = 1, limit = 20 } = req.query;
    const filter = {};

    if (department) filter.department = department;
    if (status) filter.status = status;
    if (examType) filter.examType = examType;

    const skip = (parseInt(page) - 1) * parseInt(limit);
    const [exams, total] = await Promise.all([
      Exam.find(filter)
        .populate('facultyId', 'fullName email department')
        .skip(skip)
        .limit(parseInt(limit))
        .sort({ createdAt: -1 }),
      Exam.countDocuments(filter),
    ]);

    res.status(200).json({
      success: true,
      data: exams,
      pagination: { total, page: parseInt(page), limit: parseInt(limit), pages: Math.ceil(total / limit) },
    });
  } catch (error) {
    res.status(500).json({ success: false, message: error.message });
  }
};

// GET /api/admin/results
const getAllResults = async (req, res) => {
  try {
    const { page = 1, limit = 20 } = req.query;
    const skip = (parseInt(page) - 1) * parseInt(limit);

    const [results, total] = await Promise.all([
      EvaluationResult.find()
        .populate('examId', 'subject examType department academicYear maxMarks')
        .populate('studentId', 'fullName idNumber department')
        .skip(skip)
        .limit(parseInt(limit))
        .sort({ createdAt: -1 }),
      EvaluationResult.countDocuments(),
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

module.exports = { getDashboard, getAllUsers, getUserById, createUser, updateUser, deleteUser, getAllExams, getAllResults };
