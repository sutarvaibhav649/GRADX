# routes/evaluation.py
from typing import Dict, Any, Optional, List
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, HTTPException, Body, Query
import tempfile
import os
import json

from app.services.ocr_gemini import extract_student_json
from app.models.model_answer import MODEL_ANSWERS
from app.services.evaluator import advanced_evaluator

router = APIRouter(prefix="/api/evaluation", tags=["evaluation"])

# Marks per section (total = 7)
MARKS_CONFIG = {
    "Definition": 2,
    "Body": 3,
    "Conclusion": 2
}

# Per-exam model answers: { exam_id: { question_No, topic, Answer } }
# "default" key used when no exam_id is supplied (backward compat)
MODEL_ANSWERS_STORE: Dict[str, Any] = {}

# ==================== UPLOAD MODEL ANSWER FROM IMAGE ====================
@router.post("/upload-model")
async def upload_model_answer(
    file: UploadFile = File(...),
    exam_id: str = Query(default="default", description="Exam ID to scope this model answer")
):
    """
    Upload a handwritten model answer image.
    Pass ?exam_id=<mongoId> so the model answer is stored per-exam, preventing
    concurrent faculty sessions from overwriting each other.
    """
    tmp_path = None
    try:
        suffix = os.path.splitext(file.filename or ".jpg")[1] or ".jpg"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file.flush()
            tmp_path = tmp_file.name

        print(f"Model answer image saved temporarily: {tmp_path} (exam_id={exam_id})")

        model_data = extract_student_json(tmp_path)

        model_entry = {
            "question_No": "1",
            "topic": "Extracted Model Answer",
            "Answer": model_data["Answer"]
        }

        # Store per-exam so concurrent sessions don't overwrite each other
        MODEL_ANSWERS_STORE[exam_id] = model_entry

        # Configure the evaluator with this exam's model answer
        advanced_evaluator.auto_configure_from_model(
            model_answer=model_entry,
            question_type="conceptual",
            cheating_threshold=0.4
        )

        print(f"Model answer stored for exam {exam_id}:")
        print(f"  Definition: {model_data['Answer']['Definition'][:80]}")
        print(f"  Body: {model_data['Answer']['Body'][:80]}")
        print(f"  Conclusion: {model_data['Answer']['Conclusion'][:80]}")

        return {
            "success": True,
            "message": "Model answer uploaded and configured successfully",
            "exam_id": exam_id,
            "model_extracted": model_data,
            "config": advanced_evaluator.current_config
        }

    except Exception as e:
        print(f"Error uploading model answer: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except Exception:
                pass

# ==================== GET CURRENT MODEL ANSWER ====================
@router.get("/model")
async def get_model_answer(
    exam_id: str = Query(default="default", description="Exam ID")
):
    """Get the model answer for a specific exam"""
    model_answer = MODEL_ANSWERS_STORE.get(exam_id)
    if model_answer is None:
        return {
            "success": False,
            "message": f"No model answer uploaded yet for exam {exam_id}."
        }
    return {
        "success": True,
        "exam_id": exam_id,
        "model_answer": model_answer
    }

# ==================== EVALUATE STUDENT ANSWER (Text) ====================
@router.post("/evaluate-text")
async def evaluate_text_answer(
    student_answer: Dict[str, Any] = Body(...),
    exam_id: str = Query(default="default", description="Exam ID")
):
    """
    Evaluate a text-based student answer against the uploaded model answer.
    Pass ?exam_id=<mongoId> to match the correct model answer.
    """
    try:
        model_answer = MODEL_ANSWERS_STORE.get(exam_id)
        if model_answer is None:
            raise HTTPException(
                status_code=400,
                detail=f"No model answer uploaded for exam {exam_id}. Please upload model answer first."
            )

        if not student_answer:
            raise HTTPException(status_code=400, detail="student_answer is required")

        for section in ["Definition", "Body", "Conclusion"]:
            if section not in student_answer:
                student_answer[section] = ""

        # Reconfigure evaluator with this exam's model (safe for sequential requests)
        advanced_evaluator.auto_configure_from_model(model_answer, question_type="conceptual", cheating_threshold=0.4)

        result = advanced_evaluator.evaluate(student_answer, model_answer["Answer"], MARKS_CONFIG)

        json_file = advanced_evaluator.save_to_json_file(student_answer, model_answer["Answer"], result)

        return {
            "success": True,
            "exam_id": exam_id,
            "evaluation": result,
            "saved_to_json": json_file
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== EVALUATE STUDENT ANSWER (Image) ====================
@router.post("/evaluate-image")
async def evaluate_image_answer(
    file: UploadFile = File(...),
    exam_id: str = Query(default="default", description="Exam ID")
):
    """
    Evaluate a handwritten student answer image against the uploaded model answer.
    Pass ?exam_id=<mongoId> to match the correct model answer.
    """
    tmp_path = None
    try:
        model_answer = MODEL_ANSWERS_STORE.get(exam_id)
        if model_answer is None:
            raise HTTPException(
                status_code=400,
                detail=f"No model answer uploaded for exam {exam_id}. Please upload the model answer first."
            )

        suffix = os.path.splitext(file.filename or ".jpg")[1] or ".jpg"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file.flush()
            tmp_path = tmp_file.name

        print(f"Student image saved temporarily: {tmp_path} (exam_id={exam_id})")

        student_data = extract_student_json(tmp_path)

        print(f"Extracted student answer (exam {exam_id}):")
        print(f"  Definition: {student_data['Answer']['Definition'][:80]}")
        print(f"  Body: {student_data['Answer']['Body'][:80]}")
        print(f"  Conclusion: {student_data['Answer']['Conclusion'][:80]}")

        # Reconfigure evaluator with this exam's model before scoring
        advanced_evaluator.auto_configure_from_model(model_answer, question_type="conceptual", cheating_threshold=0.4)

        result = advanced_evaluator.evaluate(student_data["Answer"], model_answer["Answer"], MARKS_CONFIG)

        json_file = advanced_evaluator.save_to_json_file(student_data["Answer"], model_answer["Answer"], result)

        return {
            "success": True,
            "exam_id": exam_id,
            "student_extracted": student_data,
            "evaluation": result,
            "saved_to_json": json_file
        }

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except Exception:
                pass
# ==================== GET EVALUATION CONFIGURATION ====================
@router.get("/config")
async def get_evaluation_config(
    exam_id: str = Query(default="default", description="Exam ID")
):
    """Get the current evaluation configuration for a given exam"""
    try:
        model_answer = MODEL_ANSWERS_STORE.get(exam_id)
        if not model_answer:
            return {
                "configured": False,
                "exam_id": exam_id,
                "message": f"No model answer uploaded for exam {exam_id}."
            }
        return {
            "configured": True,
            "exam_id": exam_id,
            "stored_exams": list(MODEL_ANSWERS_STORE.keys()),
            "config": advanced_evaluator.current_config
        }
    except Exception as e:
        return {
            "configured": False,
            "error": str(e)
        }


# ==================== GET EVALUATION HISTORY ====================
@router.get("/history")
async def get_evaluation_history(limit: int = 10):
    """
    Get evaluation history from saved JSON files
    """
    try:
        # Look for evaluation JSON files in current directory
        eval_files = []
        for file in os.listdir('.'):
            if file.startswith('evaluation_') and file.endswith('.json'):
                eval_files.append(file)
        
        # Sort by creation time (newest first)
        eval_files.sort(key=lambda x: os.path.getctime(x), reverse=True)
        
        # Limit the number of files
        eval_files = eval_files[:limit]
        
        history = []
        for file in eval_files:
            try:
                with open(file, 'r') as f:
                    data = json.load(f)
                    # Extract key information
                    if 'evaluation_result' in data:
                        result = data['evaluation_result']
                        history.append({
                            "file": file,
                            "timestamp": data.get('timestamp', ''),
                            "total_marks": result.get('total_marks', 0),
                            "max_marks": result.get('max_marks', 7),
                            "percentage": result.get('percentage', 0),
                            "section_scores": result.get('section_scores', {})
                        })
            except Exception as e:
                print(f"Error reading {file}: {e}")
                continue
        
        return {
            "count": len(history),
            "history": history
        }
    except Exception as e:
        return {
            "count": 0,
            "error": str(e),
            "history": []
        }


# ==================== CLEAR EVALUATION HISTORY ====================
@router.delete("/history")
async def clear_evaluation_history():
    """
    Clear all evaluation history JSON files
    """
    try:
        deleted = 0
        for file in os.listdir('.'):
            if file.startswith('evaluation_') and file.endswith('.json'):
                os.remove(file)
                deleted += 1
        
        return {
            "success": True,
            "message": f"Deleted {deleted} evaluation history files"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


# ==================== GET SINGLE EVALUATION BY FILE ====================
@router.get("/evaluation/{filename}")
async def get_evaluation_by_filename(filename: str):
    """
    Get a specific evaluation by filename
    """
    try:
        if not os.path.exists(filename):
            return {
                "success": False,
                "message": f"File {filename} not found"
            }
        
        with open(filename, 'r') as f:
            data = json.load(f)
        
        return {
            "success": True,
            "data": data
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

# ==================== HEALTH CHECK ====================
@router.get("/health")
async def evaluation_health():
    return {"status": "evaluation routes available"}