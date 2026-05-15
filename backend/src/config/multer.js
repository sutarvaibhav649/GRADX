const multer = require('multer');
const path = require('path');
const fs = require('fs');

const ensureDir = (dir) => {
  if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
};

const storage = multer.diskStorage({
  destination: (req, file, cb) => {
    const uploadDir = path.join(__dirname, '../../', process.env.UPLOAD_DIR || 'uploads');
    let subDir = 'misc';

    if (file.fieldname === 'studentPapers') subDir = 'student-papers';
    else if (file.fieldname === 'modelAnswer') subDir = 'model-answers';

    const dest = path.join(uploadDir, subDir);
    ensureDir(dest);
    cb(null, dest);
  },
  filename: (req, file, cb) => {
    const uniqueSuffix = `${Date.now()}-${Math.round(Math.random() * 1e9)}`;
    const ext = path.extname(file.originalname);
    cb(null, `${file.fieldname}-${uniqueSuffix}${ext}`);
  },
});

const fileFilter = (req, file, cb) => {
  const allowedMimeTypes = ['image/jpeg', 'image/png', 'image/webp', 'image/gif'];

  if (allowedMimeTypes.includes(file.mimetype)) {
    cb(null, true);
  } else {
    cb(new Error('Only JPEG, PNG, WebP, and GIF images are allowed'), false);
  }
};

const maxFileSize = process.env.MAX_FILE_SIZE
  ? parseInt(process.env.MAX_FILE_SIZE, 10)
  : 10 * 1024 * 1024;

if (isNaN(maxFileSize) || maxFileSize <= 0) {
  throw new Error('Invalid MAX_FILE_SIZE environment variable');
}

const upload = multer({
  storage,
  fileFilter,
  limits: { fileSize: maxFileSize },
});

module.exports = upload;
