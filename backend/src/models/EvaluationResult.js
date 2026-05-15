const mongoose = require('mongoose');

const questionMarkSchema = new mongoose.Schema(
  {
    questionNumber: { type: Number, required: true },
    marksObtained: { type: Number, required: true, min: 0 },
    maxMarks: { type: Number, required: true, min: 0 },
    aiScore: { type: Number },
    manualAdjustment: { type: Number, default: 0 },
    remarks: { type: String, trim: true },
  },
  { _id: false }
);

const evaluationResultSchema = new mongoose.Schema(
  {
    examId: {
      type: mongoose.Schema.Types.ObjectId,
      ref: 'Exam',
      required: true,
    },
    studentId: {
      type: mongoose.Schema.Types.ObjectId,
      ref: 'User',
      required: true,
    },
    studentAnswerSheet: {
      email: String,
      filePath: String,
      originalName: String,
    },
    questionWiseMarks: [questionMarkSchema],
    totalMarksObtained: {
      type: Number,
      default: 0,
    },
    maxMarks: {
      type: Number,
      required: true,
    },
    aiScore: {
      type: Number,
    },
    manualAdjustment: {
      type: Number,
      default: 0,
    },
    finalScore: {
      type: Number,
    },
    percentage: {
      type: Number,
    },
    grade: {
      type: String,
      enum: ['O', 'A+', 'A', 'B+', 'B', 'C', 'F', 'N/A'],
      default: 'N/A',
    },
    crossCheckRequired: {
      type: Boolean,
      default: false,
    },
    crossCheckCompleted: {
      type: Boolean,
      default: false,
    },
    crossCheckNotes: {
      type: String,
      trim: true,
    },
    evaluationStatus: {
      type: String,
      enum: ['pending', 'ai_evaluated', 'manually_reviewed', 'finalized'],
      default: 'pending',
    },
    evaluatedAt: {
      type: Date,
    },
    reviewedBy: {
      type: mongoose.Schema.Types.ObjectId,
      ref: 'User',
    },
    reviewedAt: {
      type: Date,
    },
    extractedAnswer: {
      Definition: { type: String, default: '' },
      Body: { type: String, default: '' },
      Conclusion: { type: String, default: '' },
    },
    aiEvaluationDetails: {
      type: mongoose.Schema.Types.Mixed,
    },
    usedMockEvaluation: {
      type: Boolean,
      default: false,
    },
  },
  { timestamps: true }
);

evaluationResultSchema.pre('save', function (next) {
  if (this.finalScore !== undefined && this.maxMarks) {
    this.percentage = parseFloat(((this.finalScore / this.maxMarks) * 100).toFixed(2));
    this.grade = calculateGrade(this.percentage);
  }
  next();
});

function calculateGrade(percentage) {
  if (percentage >= 90) return 'O';
  if (percentage >= 80) return 'A+';
  if (percentage >= 70) return 'A';
  if (percentage >= 60) return 'B+';
  if (percentage >= 50) return 'B';
  if (percentage >= 40) return 'C';
  if (percentage < 40) return 'F';
  return 'N/A';
}

module.exports = mongoose.model('EvaluationResult', evaluationResultSchema);
