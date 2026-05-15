# routes/evaluation.py - Updated with model answer upload
from typing import Dict, Any, Optional, List
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, HTTPException, Body
from typing import Dict, Any, Optional
import tempfile
import os
import json
from datetime import datetime

from app.services.ocr_gemini import extract_student_json
from app.models.model_answer import MODEL_ANSWER, MODEL_ANSWERS
from app.services.evaluator import advanced_evaluator

router = APIRouter(prefix="/api/evaluation", tags=["evaluation"])

# Fixed marks for 7-mark question
MARKS_CONFIG = {
    "Definition": 2,
    "Body": 3,
    "Conclusion": 2
}

# Store model answer globally after upload
current_model_answer = None

# ==================== UPLOAD MODEL ANSWER FROM IMAGE ====================
@router.post("/upload-model")
async def upload_model_answer(
    file: UploadFile = File(...)
):
    """
    Upload a handwritten model answer image.
    This will be used as the reference for all student evaluations.
    """
    tmp_path = None
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file.flush()
            tmp_path = tmp_file.name
        
        print(f"📸 Model answer image saved to: {tmp_path}")
        
        # Extract model answer from image using OCR
        model_data = extract_student_json(tmp_path)
        
        # Store globally
        global current_model_answer
        current_model_answer = {
            "question_No": "1",
            "topic": "Extracted Model Answer",
            "Answer": model_data["Answer"]
        }
        
        # Auto-configure the evaluator with this model answer
        advanced_evaluator.auto_configure_from_model(
            model_answer=current_model_answer,
            question_type="conceptual",
            cheating_threshold=0.4
        )
        
        print(f"✅ Model answer extracted and configured:")
        print(f"   Definition: {model_data['Answer']['Definition'][:100]}...")
        print(f"   Body: {model_data['Answer']['Body'][:100]}...")
        print(f"   Conclusion: {model_data['Answer']['Conclusion'][:100]}...")
        
        return {
            "success": True,
            "message": "Model answer uploaded and configured successfully",
            "model_extracted": model_data,
            "config": advanced_evaluator.current_config
        }
        
    except Exception as e:
        print(f"❌ Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except:
                pass

# ==================== GET CURRENT MODEL ANSWER ====================
@router.get("/model")
async def get_model_answer():
    """Get the currently loaded model answer"""
    if current_model_answer is None:
        return {
            "success": False,
            "message": "No model answer uploaded yet. Please upload one first."
        }
    
    return {
        "success": True,
        "model_answer": current_model_answer
    }

# ==================== EVALUATE STUDENT ANSWER (Text) ====================
@router.post("/evaluate-text")
async def evaluate_text_answer(student_answer: Dict[str, Any] = Body(...)):
    """
    Evaluate a text-based student answer
    
    Expected JSON format:
    {
        "Definition": "Student's definition text...",
        "Body": "Student's body text...",
        "Conclusion": "Student's conclusion text..."
    }
    """
    try:
        if current_model_answer is None:
            raise HTTPException(status_code=400, detail="No model answer uploaded. Please upload model answer first.")
        
        if not student_answer:
            raise HTTPException(status_code=400, detail="student_answer is required")
        
        required_sections = ["Definition", "Body", "Conclusion"]
        for section in required_sections:
            if section not in student_answer:
                student_answer[section] = ""
        
        result = advanced_evaluator.evaluate(
            student_answer,
            current_model_answer["Answer"],
            MARKS_CONFIG
        )
        
        json_file = advanced_evaluator.save_to_json_file(
            student_answer,
            current_model_answer["Answer"],
            result
        )
        
        return {
            "success": True,
            "evaluation": result,
            "saved_to_json": json_file
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== EVALUATE STUDENT ANSWER (Image) ====================
@router.post("/evaluate-image")
async def evaluate_image_answer(
    file: UploadFile = File(...)
):
    """
    Evaluate a handwritten student answer from image
    """
    tmp_path = None
    try:
        if current_model_answer is None:
            raise HTTPException(status_code=400, detail="No model answer uploaded. Please upload model answer first.")
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file.flush()
            tmp_path = tmp_file.name
        
        print(f"📸 Student image saved to: {tmp_path}")
        
        # Extract student answer from image using OCR
        student_data = extract_student_json(tmp_path)
        
        print(f"📝 Extracted student answer:")
        print(f"   Definition: {student_data['Answer']['Definition'][:100]}...")
        print(f"   Body: {student_data['Answer']['Body'][:100]}...")
        print(f"   Conclusion: {student_data['Answer']['Conclusion'][:100]}...")
        
        # Evaluate
        result = advanced_evaluator.evaluate(
            student_data["Answer"],
            current_model_answer["Answer"],
            MARKS_CONFIG
        )
        
        # Save to JSON
        json_file = advanced_evaluator.save_to_json_file(
            student_data["Answer"],
            current_model_answer["Answer"],
            result
        )
        
        return {
            "success": True,
            "student_extracted": student_data,
            "evaluation": result,
            "saved_to_json": json_file
        }
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except:
                pass
# ==================== GET EVALUATION CONFIGURATION ====================
@router.get("/config")
async def get_evaluation_config():
    """
    Get the current evaluation configuration
    """
    try:
        if not advanced_evaluator.current_config:
            return {
                "configured": False,
                "message": "No configuration loaded. Please upload a model answer first."
            }
        
        return {
            "configured": True,
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