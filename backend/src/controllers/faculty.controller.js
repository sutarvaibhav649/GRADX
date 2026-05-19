const path = require('path');
const Exam = require('../models/Exam');
const EvaluationResult = require('../models/EvaluationResult');
const User = require('../models/User');

// GET /api/faculty/dashboard
const getDashboard = async (req, res) => {
  try {
    if (!req.user || !req.user._id) {
      return res.status(401).json({ success: false, message: 'User authentication failed' });
    }

    const exams = await Exam.find({ facultyId: req.user._id });

    const aiEvaluated = exams.filter((e) => e.evaluationMode === 'ai' && e.status === 'completed').length;
    const manuallyEvaluated = exams.filter((e) => e.evaluationMode === 'manual' && e.status === 'completed').length;

    const recentExams = await Exam.find({ facultyId: req.user._id })
      .sort({ createdAt: -1 })
      .limit(5);

    res.status(200).json({
      success: true,
      data: {
        stats: {
          papersUploaded: exams.length,
          aiEvaluated,
          manuallyEvaluated,
          pendingEvaluation: exams.filter((e) => e.status === 'pending').length,
          inProgress: exams.filter((e) => e.status === 'in_progress').length,
        },
        recentExams,
      },
    });
  } catch (error) {
    res.status(500).json({ success: false, message: error.message });
  }
};

// POST /api/faculty/exams
const createExam = async (req, res) => {
  try {
    if (!req.user || !req.user._id) {
      return res.status(401).json({ success: false, message: 'User authentication failed' });
    }

    const {
      academicYear,
      year,
      department,
      examType,
      semester,
      maxMarks,
      subject,
      evaluationMode,
      enableCrossCheck,
      evaluationStrictness,
    } = req.body;

    const rawStudentEmails = req.body.studentEmails || [];
    const studentEmails = Array.isArray(rawStudentEmails)
      ? rawStudentEmails
      : [rawStudentEmails];

    const studentFiles = (req.files?.studentPapers || [])
      .filter(f => f && f.path && f.originalname);

    if (studentFiles.length !== studentEmails.length) {
      return res.status(400).json({
        success: false,
        message: 'Each student answer sheet must be submitted with a corresponding email address',
      });
    }

    const studentPapers = studentFiles.map((f, index) => ({
      email: String(studentEmails[index] || '').trim(),
      filePath: process.env.STUDENT_PAPER_PATH + '/' + path.basename(f.path),
      originalName: f.originalname,
    }));

    const modelAnswerFile = req.files?.modelAnswer?.[0];
    if (!modelAnswerFile || !modelAnswerFile.path) {
      return res.status(400).json({ 
        success: false, 
        message: 'Model answer Image is required' 
      });
    }
    const modelAnswer = {
      filePath: process.env.MODEL_PAPER_PATH + '/' + path.basename(modelAnswerFile.path),
      originalName: modelAnswerFile.originalname,
    };

    if (studentPapers.length === 0) {
      return res.status(400).json({ success: false, message: 'At least one student answer sheet is required' });
    }

    if (studentPapers.some((paper) => !paper.email)) {
      return res.status(400).json({ success: false, message: 'Every student answer sheet requires a corresponding student email' });
    }

    const marks = parseInt(maxMarks);
    if (isNaN(marks) || marks < 1 || marks > 500) {
      return res.status(400).json({ 
        success: false, 
        message: 'Max marks must be between 1 and 500' 
      });
    }

    // ── Parse question config ────────────────────────────────────────────────
    let questions = [];       // single-question mode: flat sections
    let questionSet = [];     // multi-question mode: questions with own sections
    let isMultiQuestion = false;

    // Multi-question mode: questionSet JSON [{ number, text, sections:[{name,marks}] }]
    if (req.body.questionSet) {
      try {
        const parsed = JSON.parse(req.body.questionSet);
        if (Array.isArray(parsed) && parsed.length > 0) {
          questionSet = parsed.map(q => ({
            questionNumber: Number(q.number || q.questionNumber || 1),
            questionText:   String(q.text || q.questionText || '').trim(),
            sections: (q.sections || [])
              .map(s => ({
                sectionName: String(s.name || s.sectionName || '').trim(),
                maxMarks:    Number(s.marks ?? s.maxMarks ?? 0),
              }))
              .filter(s => s.sectionName && s.maxMarks > 0),
          })).filter(q => q.sections.length > 0);
          isMultiQuestion = questionSet.length > 0;
        }
      } catch (e) { /* ignore */ }
    }

    // Single-question mode: questions JSON [{ name, marks }]
    if (!isMultiQuestion && req.body.questions) {
      try {
        const parsed = JSON.parse(req.body.questions);
        if (Array.isArray(parsed) && parsed.length > 0) {
          questions = parsed.map(q => ({
            sectionName: String(q.name || q.sectionName || '').trim(),
            maxMarks:    Number(q.marks ?? q.maxMarks ?? 0),
          })).filter(q => q.sectionName && q.maxMarks > 0);
        }
      } catch (e) { /* ignore */ }
    }

    // Effective max marks = sum of all section marks
    let effectiveMaxMarks = marks;
    if (isMultiQuestion) {
      effectiveMaxMarks = questionSet.reduce(
        (sum, q) => sum + q.sections.reduce((s2, sec) => s2 + sec.maxMarks, 0), 0
      ) || marks;
    } else if (questions.length > 0) {
      effectiveMaxMarks = questions.reduce((sum, q) => sum + q.maxMarks, 0);
    }

    const exam = await Exam.create({
      facultyId: req.user._id,
      academicYear,
      year,
      department,
      examType,
      semester,
      maxMarks: effectiveMaxMarks,
      subject,
      questions,
      isMultiQuestion,
      questionSet,
      studentAnswerSheets: studentPapers,
      modelAnswer,
      evaluationMode,
      enableCrossCheck: enableCrossCheck === 'true' || enableCrossCheck === true,
      evaluationStrictness,
      totalStudents: studentPapers.length,
    });

    res.status(201).json({ success: true, data: exam, message: 'Exam created successfully' });
  } catch (error) {
    res.status(500).json({ success: false, message: error.message });
  }
};

// GET /api/faculty/exams
const getMyExams = async (req, res) => {
  try {
    const { status, examType, department, page = 1, limit = 10 } = req.query;
    const filter = { facultyId: req.user._id };

    if (status) filter.status = status;
    if (examType) filter.examType = examType;
    if (department) filter.department = department;

    const skip = (parseInt(page) - 1) * parseInt(limit);
    const [exams, total] = await Promise.all([
      Exam.find(filter).skip(skip).limit(parseInt(limit)).sort({ createdAt: -1 }),
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

// GET /api/faculty/exams/:id
const getExamById = async (req, res) => {
  try {
    const exam = await Exam.findOne({ _id: req.params.id, facultyId: req.user._id });
    if (!exam) return res.status(404).json({ success: false, message: 'Exam not found' });

    const results = await EvaluationResult.find({ examId: exam._id })
      .populate('studentId', 'fullName idNumber department');

    res.status(200).json({ success: true, data: { exam, results } });
  } catch (error) {
    res.status(500).json({ success: false, message: error.message });
  }
};

// PUT /api/faculty/exams/:id
const updateExam = async (req, res) => {
  try {
    const exam = await Exam.findOne({ _id: req.params.id, facultyId: req.user._id });
    if (!exam) return res.status(404).json({ success: false, message: 'Exam not found' });

    if (exam.status !== 'pending') {
      return res.status(400).json({ success: false, message: 'Only pending exams can be updated' });
    }

    const allowedFields = ['evaluationMode', 'enableCrossCheck', 'evaluationStrictness', 'subject'];
    allowedFields.forEach((field) => {
      if (req.body[field] !== undefined) exam[field] = req.body[field];
    });

    await exam.save();
    res.status(200).json({ success: true, data: exam });
  } catch (error) {
    res.status(500).json({ success: false, message: error.message });
  }
};

// DELETE /api/faculty/exams/:id
const deleteExam = async (req, res) => {
  try {
    const exam = await Exam.findOne({ _id: req.params.id, facultyId: req.user._id });
    if (!exam) return res.status(404).json({ success: false, message: 'Exam not found' });

    if (exam.status !== 'pending') {
      return res.status(400).json({ success: false, message: 'Only pending exams can be deleted' });
    }

    await EvaluationResult.deleteMany({ examId: exam._id });
    await exam.deleteOne();

    res.status(200).json({ success: true, message: 'Exam deleted successfully' });
  } catch (error) {
    res.status(500).json({ success: false, message: error.message });
  }
};

// GET /api/faculty/exams/:id/results
const getExamResults = async (req, res) => {
  try {
    const exam = await Exam.findOne({ _id: req.params.id, facultyId: req.user._id });
    if (!exam) return res.status(404).json({ success: false, message: 'Exam not found' });

    const results = await EvaluationResult.find({ examId: exam._id })
      .populate('studentId', 'fullName idNumber department email');

    res.status(200).json({ success: true, data: results });
  } catch (error) {
    res.status(500).json({ success: false, message: error.message });
  }
};

module.exports = { getDashboard, createExam, getMyExams, getExamById, updateExam, deleteExam, getExamResults };
