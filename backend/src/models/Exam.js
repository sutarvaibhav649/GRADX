const mongoose = require('mongoose');

const examSchema = new mongoose.Schema(
  {
    facultyId: {
      type: mongoose.Schema.Types.ObjectId,
      ref: 'User',
      required: true,
    },
    academicYear: {
      type: String,
      required: [true, 'Academic year is required'],
      enum: ['2025-26', '2024-25', '2023-24'],
    },
    year: {
      type: String,
      required: [true, 'Year is required'],
      enum: ['first', 'second', 'third', 'fourth'],
    },
    department: {
      type: String,
      required: [true, 'Department is required'],
      enum: ['cse', 'aiml', 'ds', 'it', 'ece'],
    },
    examType: {
      type: String,
      required: [true, 'Exam type is required'],
      enum: ['mse', 'ese', 'makeup', 'quiz'],
    },
    semester: {
      type: String,
      required: [true, 'Semester is required'],
      enum: ['odd', 'even'],
    },
    maxMarks: {
      type: Number,
      required: [true, 'Max marks is required'],
      min: 1,
    },
    subject: {
      type: String,
      required: [true, 'Subject is required'],
      trim: true,
    },
    studentAnswerSheets: [
      {
        email: String,
        filePath: String,
        originalName: String,
        uploadedAt: { type: Date, default: Date.now },
      },
    ],
    modelAnswer: {
      filePath: String,
      originalName: String,
    },
    evaluationMode: {
      type: String,
      enum: ['ai', 'manual'],
      required: true,
    },
    enableCrossCheck: {
      type: Boolean,
      default: false,
    },
    evaluationStrictness: {
      type: String,
      enum: ['lenient', 'moderate', 'strict'],
      default: 'moderate',
    },
    status: {
      type: String,
      enum: ['pending', 'in_progress', 'completed'],
      default: 'pending',
    },
    totalStudents: {
      type: Number,
      default: 0,
    },
    evaluatedCount: {
      type: Number,
      default: 0,
    },
    // Single-question mode: flat list of sections (backward-compatible)
    questions: [
      {
        sectionName: { type: String, required: true, trim: true },
        maxMarks: { type: Number, required: true, min: 0 },
      },
    ],
    // Multi-question mode: each question has its own sections
    isMultiQuestion: {
      type: Boolean,
      default: false,
    },
    questionSet: [
      {
        questionNumber: { type: Number, required: true },
        questionText:   { type: String, default: '' },
        sections: [
          {
            sectionName: { type: String, required: true, trim: true },
            maxMarks:    { type: Number, required: true, min: 0 },
          },
        ],
        modelAnswerExtracted: {
          type: mongoose.Schema.Types.Mixed,
          default: {},
        },
      },
    ],
    modelAnswerUploadedToAI: {
      type: Boolean,
      default: false,
    },
    modelAnswerExtracted: {
      type: mongoose.Schema.Types.Mixed,
      default: {},
    },
  },
  { timestamps: true }
);

module.exports = mongoose.model('Exam', examSchema);
