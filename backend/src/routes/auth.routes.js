const express = require('express');
const { body } = require('express-validator');
const { signup, login, getMe, updateProfile, changePassword } = require('../controllers/auth.controller');
const { protect } = require('../middleware/auth.middleware');

const router = express.Router();

const signupValidation = [
  body('fullName').trim().notEmpty().withMessage('Full name is required'),
  body('email').isEmail().withMessage('Valid email is required').normalizeEmail(),
  body('password').isLength({ min: 8 }).withMessage('Password must be at least 8 characters'),
  body('confirmPassword').custom((value, { req }) => {
    if (value !== req.body.password) throw new Error('Passwords do not match');
    return true;
  }),
  body('role').isIn(['student', 'faculty', 'admin']).withMessage('Role must be student, faculty, or admin'),
  body('idNumber').trim().notEmpty().withMessage('ID number is required'),
  body('department')
    .if((value, { req }) => req.body.role !== 'admin')
    .isIn(['cse', 'aiml', 'ds', 'it', 'ece'])
    .withMessage('Valid department is required'),
];

const loginValidation = [
  body('email').isEmail().withMessage('Valid email is required').normalizeEmail(),
  body('password').notEmpty().withMessage('Password is required'),
  body('role').isIn(['student', 'faculty', 'admin']).withMessage('Role is required'),
];

const profileValidation = [
  body('fullName').trim().notEmpty().withMessage('Full name is required'),
  body('idNumber').trim().notEmpty().withMessage('ID number is required'),
  body('department')
    .if((value, { req }) => req.user?.role !== 'admin')
    .isIn(['cse', 'aiml', 'ds', 'it', 'ece'])
    .withMessage('Valid department is required'),
  body('sendProdUpdate').optional().isBoolean().withMessage('Product updates must be true or false'),
];

router.post('/signup', signupValidation, signup);
router.post('/login', loginValidation, login);
router.get('/me', protect, getMe);
router.put('/profile', protect, profileValidation, updateProfile);
router.put('/change-password', protect, changePassword);

module.exports = router;
