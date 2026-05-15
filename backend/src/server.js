require('dotenv').config({ path: require('path').join(__dirname, '../.env') });

// Validate required environment variables
const requiredEnvVars = ['MONGO_URI', 'JWT_SECRET', 'JWT_EXPIRES_IN'];
const missing = requiredEnvVars.filter(v => !process.env[v]);

if (missing.length > 0) {
  console.error(`Missing required environment variables: ${missing.join(', ')}`);
  process.exit(1);
}

const express = require('express');
const cors = require('cors');
const path = require('path');
const connectDB = require('./config/database');

const authRoutes = require('./routes/auth.routes');
const adminRoutes = require('./routes/admin.routes');
const studentRoutes = require('./routes/student.routes');
const facultyRoutes = require('./routes/faculty.routes');
const evaluationRoutes = require('./routes/evaluation.routes');

connectDB();

const app = express();

app.use(cors({ origin: process.env.CORS_ORIGIN || 'http://localhost:4200', credentials: true }));
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Serve uploaded files statically
app.use('/uploads', express.static(path.join(__dirname, '../uploads')));

app.use('/api/auth', authRoutes);
app.use('/api/admin', adminRoutes);
app.use('/api/student', studentRoutes);
app.use('/api/faculty', facultyRoutes);
app.use('/api/evaluation', evaluationRoutes);

app.get('/api/health', (req, res) => {
  res.json({ success: true, message: 'GRADX API is running', timestamp: new Date() });
});

app.use((req, res) => {
  res.status(404).json({ success: false, message: `Route ${req.originalUrl} not found` });
});

app.use((err, req, res, next) => {
  console.error('Unexpected error:', err);  // Log full error
  if (err.code === 'LIMIT_FILE_SIZE') {
    return res.status(400).json({ success: false, message: 'File size exceeds limit (10MB max)' });
  }
  if (err.message === 'Only Images files are allowed') {
    return res.status(400).json({ success: false, message: err.message });
  }
  res.status(500).json({ 
    success: false, 
    message: 'An error occurred. Please try again later.',
    ...(process.env.NODE_ENV === 'development' && { error: err.message })
  });
});

const PORT = process.env.PORT || 5000;
app.listen(PORT, () => {
  console.log(`GRADX backend running on http://localhost:${PORT}`);
});
