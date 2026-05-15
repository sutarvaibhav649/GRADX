# ocr_gemini.py - OpenRouter version (works with Gemini & other models)

import openai
import os
import re
import json
import base64
from PIL import Image
from io import BytesIO

# Configure OpenRouter (OpenAI-compatible endpoint)
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# Use Gemini 2.5 Flash via OpenRouter (cheaper options also available)
MODEL_NAME = os.getenv("OCR_MODEL", "google/gemini-2.5-flash")

# Initialize OpenAI client pointing to OpenRouter
client = openai.OpenAI(
    base_url=OPENROUTER_BASE_URL,
    api_key=OPENROUTER_API_KEY,
)

# Optional: Set your site info for OpenRouter rankings
YOUR_SITE_URL = os.getenv("YOUR_SITE_URL", "http://localhost:8000")
YOUR_SITE_NAME = os.getenv("YOUR_SITE_NAME", "AI Evaluator")

print(f"✅ OCR initialized with model: {MODEL_NAME} via OpenRouter")

PROMPT = """
You are an OCR system for evaluating student answers.

Extract ONLY Definition, Body, and Conclusion from the handwritten answer.

STRICT RULES:
- Output ONLY valid JSON
- Do NOT add explanations
- Do NOT wrap in markdown
- Do NOT add extra text
- Missing fields must be empty string ""
- Preserve the student's exact wording as much as possible

JSON FORMAT:
{
  "question_No": "1",
  "Answer": {
    "Definition": "",
    "Body": "",
    "Conclusion": ""
  }
}

Return ONLY the JSON.
"""

def encode_image_to_base64(image_path: str) -> str:
    """Convert image to base64 for API call"""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def extract_student_json(image_path: str) -> dict:
    """
    Extract student answer from image using OpenRouter API
    
    Args:
        image_path: Path to the image file
        
    Returns:
        Dictionary with question_No and Answer fields
    """
    try:
        print(f"📸 Processing image: {image_path}")
        
        # Open and verify image
        image = Image.open(image_path)
        print(f"   Image size: {image.size}, Mode: {image.mode}")
        
        # Encode image to base64
        base64_image = encode_image_to_base64(image_path)
        
        # Call OpenRouter with image
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": PROMPT},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            extra_headers={
                "HTTP-Referer": YOUR_SITE_URL,
                "X-Title": YOUR_SITE_NAME,
            },
            max_tokens=4096,
            temperature=0.1,
        )
        
        # Extract response text
        text = response.choices[0].message.content.strip()
        
        print(f"📝 OpenRouter response length: {len(text)} characters")
        
        # Extract JSON from response
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            print("⚠️ No JSON found in response")
            return {
                "question_No": "1",
                "Answer": {
                    "Definition": text[:500] if text else "",
                    "Body": "",
                    "Conclusion": ""
                }
            }
        
        json_str = match.group(0)
        
        # Parse JSON
        try:
            result = json.loads(json_str)
            
            # Ensure all fields exist
            if "Answer" not in result:
                result["Answer"] = {}
            
            for section in ["Definition", "Body", "Conclusion"]:
                if section not in result["Answer"]:
                    result["Answer"][section] = ""
                elif result["Answer"][section] == " ":
                    result["Answer"][section] = ""
            
            print(f"✅ Extracted: Definition={len(result['Answer']['Definition'])} chars, "
                  f"Body={len(result['Answer']['Body'])} chars, "
                  f"Conclusion={len(result['Answer']['Conclusion'])} chars")
            
            return result
            
        except json.JSONDecodeError as e:
            print(f"❌ JSON parse error: {e}")
            return {
                "question_No": "1",
                "Answer": {
                    "Definition": json_str[:500],
                    "Body": "",
                    "Conclusion": ""
                }
            }
            
    except Exception as e:
        print(f"❌ OCR Error: {e}")
        raise ValueError(f"Failed to extract text from image: {e}")