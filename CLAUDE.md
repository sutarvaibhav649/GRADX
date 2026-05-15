# GRADX — AI Answer-Sheet Evaluation System

## Architecture (3 services)

| Service | Tech | Port | Purpose |
|---|---|---|---|
| `backend-python/` | FastAPI + SentenceTransformers | 8000 | OCR + AI evaluation engine |
| `backend/` | Node.js + Express + MongoDB | 5000 | Auth, business logic, file storage |
| `frontend/` | Angular 21 (standalone) | 4200 | Role-based UI (admin/faculty/student) |

## Start Commands

```bash
# Python backend (run from backend-python/)
$env:PYTHONUTF8="1"; python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Node backend (run from backend/)
npm start   # or: node src/server.js

# Angular (run from frontend/)
npm start
```

## Environment Variables

### `backend-python/.env`
- `OPENROUTER_API_KEY` — required, calls google/gemini-2.5-flash for OCR
- `OCR_MODEL` — default `google/gemini-2.5-flash`
- `PORT` — default 8000

### `backend/.env`
- `MONGO_URI` — MongoDB connection string
- `JWT_SECRET` — JWT signing secret
- `FASTAPI_URL` — default `http://localhost:8000`
- `CORS_ORIGIN` — default `http://localhost:4200`
- `STUDENT_PAPER_PATH` — `/uploads/student-papers`
- `MODEL_PAPER_PATH` — `/uploads/model-answers`
- `MAX_FILE_SIZE` — 10485760 (10MB)

## Roles
- **admin**: view all users/exams/results
- **faculty**: create exams, upload answer sheets, trigger AI evaluation, cross-check
- **student**: view own results

## Key Data Flow

1. Faculty uploads exam (student PDFs + model answer image) → `POST /api/faculty/exams`
2. Faculty triggers evaluation → `POST /api/evaluation/start/:examId`
3. Node uploads model answer to FastAPI → `POST http://localhost:8000/api/evaluation/upload-model`
   - FastAPI OCRs image via OpenRouter → stores model answer globally → configures evaluator
4. Node sends each student image to FastAPI → `POST http://localhost:8000/api/evaluation/evaluate-image`
   - FastAPI OCRs image → evaluates Definition/Body/Conclusion via SentenceTransformers (all-mpnet-base-v2)
   - Returns: `{ total_marks, max_marks:7, percentage, section_scores, feedback, student_extracted }`
5. Node scales FastAPI marks to `exam.maxMarks`, saves `EvaluationResult` to MongoDB
6. If `enableCrossCheck`: frontend shows cross-check modal with extracted text + per-section scores
7. Faculty can adjust marks → `PUT /api/evaluation/results/:id`
8. Faculty finalizes → `PUT /api/evaluation/results/:examId/finalize`
9. Students view results → `GET /api/student/results/:id`

## API Routes Summary

### Node.js (port 5000)
```
POST   /api/auth/signup
POST   /api/auth/login
GET    /api/auth/me
PUT    /api/auth/change-password

GET    /api/admin/dashboard
GET    /api/admin/users
GET    /api/admin/exams
GET    /api/admin/results

GET    /api/faculty/dashboard
POST   /api/faculty/exams           ← multipart: studentPapers[], studentEmails[], modelAnswer
GET    /api/faculty/exams
GET    /api/faculty/exams/:id
PUT    /api/faculty/exams/:id
DELETE /api/faculty/exams/:id
GET    /api/faculty/exams/:id/results

GET    /api/student/dashboard
GET    /api/student/results
GET    /api/student/results/:id

POST   /api/evaluation/start/:examId          ← triggers full AI pipeline
POST   /api/evaluation/upload-model/:examId
GET    /api/evaluation/exam/:examId
PUT    /api/evaluation/results/:id            ← manual mark adjustment
PUT    /api/evaluation/results/:id/finalize
GET    /api/evaluation/results/:id
```

### FastAPI (port 8000)
```
POST   /api/evaluation/upload-model    ← file upload; sets global model answer
POST   /api/evaluation/evaluate-image  ← file upload; returns evaluation JSON
POST   /api/evaluation/evaluate-text   ← JSON body
GET    /api/evaluation/model
GET    /api/evaluation/config
GET    /api/evaluation/history
DELETE /api/evaluation/history
GET    /health
```

## Database Models

### User
`fullName, email(unique), password(hashed), role(student/faculty/admin), idNumber(unique), department(cse/aiml/ds/it/ece), isActive`

### Exam
`facultyId, academicYear, year, department, examType(mse/ese/makeup/quiz), semester, maxMarks, subject, studentAnswerSheets[{email,filePath}], modelAnswer{filePath}, evaluationMode(ai/manual), enableCrossCheck, evaluationStrictness(lenient/moderate/strict), status(pending/in_progress/completed), modelAnswerUploadedToAI`

### EvaluationResult
`examId, studentId, studentAnswerSheet, questionWiseMarks[{questionNumber,marksObtained,maxMarks,aiScore}], totalMarksObtained, maxMarks, aiScore, finalScore, percentage, grade(O/A+/A/B+/B/C/F), crossCheckRequired, evaluationStatus(pending/ai_evaluated/manually_reviewed/finalized), extractedAnswer{Definition,Body,Conclusion}, aiEvaluationDetails`

## FastAPI Evaluation Logic
- OCR model: OpenRouter → google/gemini-2.5-flash
- Embedding model: all-mpnet-base-v2 (sentence-transformers)
- Scoring per section: `0.5*semantic_sim + 0.25*concept_coverage + 0.25*depth_score` × coherence
- Default marks config: Definition=2, Body=3, Conclusion=2 (total 7)
- FastAPI always returns marks out of 7; Node.js scales to `exam.maxMarks`
- Cheating detection: keyword density > 0.6 → 20% penalty

## Frontend Structure
- `src/app/auth/` — login, signup
- `src/app/faculty/faculty-dashboard/` — exam creation, AI evaluation trigger, cross-check modal
- `src/app/student/student-dashboard/` — results view
- `src/app/admin/admin-dashboard/` — system overview
- `src/app/shared/services/` — auth, faculty, student, admin services
- `src/app/shared/interceptors/` — auth (adds Bearer token), error (toast on HTTP errors)
- `src/environments/environment.ts` — `apiUrl: 'http://localhost:5000/api'`

## Key Design Decisions
- FastAPI is **stateful**: model answer is stored in memory per process restart. Re-upload required if Python service restarts.
- Student must be registered in MongoDB for evaluation result to be saved. Unregistered student emails are skipped.
- `insertMany` is used in `startEvaluation` — does NOT trigger Mongoose `pre('save')` hooks. Percentage/grade are set explicitly.
- Cross-check modal uses direct DOM manipulation (not Angular bindings) — keep as-is unless refactoring.
- `enableCrossCheck=true` shows the modal for ALL evaluated students, regardless of `crossCheckRequired` flag.

## File Upload Paths
- Student papers: `backend/uploads/student-papers/`
- Model answers: `backend/uploads/model-answers/`
- Stored in DB as: `/uploads/student-papers/<filename>` (env var prefix)
- Resolved on disk via `path.resolve(__dirname, '../..') + '/uploads/...'`
