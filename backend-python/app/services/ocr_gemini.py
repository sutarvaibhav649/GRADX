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

print(f"[OK] OCR initialized with model: {MODEL_NAME} via OpenRouter")

DEFAULT_SECTIONS = ["Definition", "Body", "Conclusion"]


def make_extraction_prompt(section_names: list) -> str:
    import json as _json
    empty_answer = {name: "" for name in section_names}
    template = _json.dumps({"question_No": "1", "Answer": empty_answer}, indent=2)
    section_list = ", ".join(f'"{s}"' for s in section_names)
    return f"""You are an OCR system for evaluating student handwritten answers.

Extract content for each of these sections: {section_list}

STRICT RULES:
- Output ONLY valid JSON — no markdown, no explanations, nothing else
- If the student wrote section headings/labels, extract the text under each heading into the correct section
- If NO clear headings exist, copy the student's COMPLETE answer text into EVERY section
  (Do NOT split the answer by position — the evaluator will find relevant content per section)
- Illegible or unclear words: write your best guess inside [brackets]
- Preserve the student's exact wording as closely as possible

Return ONLY this JSON:
{template}"""

def encode_image_to_base64(image_path: str) -> str:
    """Convert image to base64 for API call"""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def extract_student_json(image_path: str, section_names: list = None) -> dict:
    """
    Extract student answer sections from a handwritten image via OpenRouter.

    Args:
        image_path:    Path to the image file
        section_names: Sections to extract (default: Definition/Body/Conclusion)

    Returns:
        Dict with question_No and Answer keys
    """
    if not section_names:
        section_names = DEFAULT_SECTIONS

    prompt = make_extraction_prompt(section_names)

    try:
        print(f"[IMG] Processing image: {image_path}")
        image = Image.open(image_path)
        print(f"   Image size: {image.size}, Mode: {image.mode}")

        base64_image = encode_image_to_base64(image_path)

        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
                        }
                    ]
                }
            ],
            extra_headers={
                "HTTP-Referer": YOUR_SITE_URL,
                "X-Title": YOUR_SITE_NAME,
            },
            max_tokens=2048,
            temperature=0.1,
        )

        text = response.choices[0].message.content.strip()
        print(f"[RES] OpenRouter response length: {len(text)} characters")

        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            print("[WARN] No JSON found in response")
            fallback = {s: "" for s in section_names}
            fallback[section_names[0]] = text[:500] if text else ""
            return {"question_No": "1", "Answer": fallback}

        json_str = match.group(0)
        try:
            result = json.loads(json_str)
            if "Answer" not in result:
                result["Answer"] = {}
            for section in section_names:
                if section not in result["Answer"]:
                    result["Answer"][section] = ""
                elif result["Answer"][section] == " ":
                    result["Answer"][section] = ""

            summary = ", ".join(
                f"{s}={len(result['Answer'].get(s, ''))} chars" for s in section_names
            )
            print(f"[OK] Extracted: {summary}")
            return result

        except json.JSONDecodeError as e:
            print(f"[ERR] JSON parse error: {e}")
            fallback = {s: "" for s in section_names}
            fallback[section_names[0]] = json_str[:500]
            return {"question_No": "1", "Answer": fallback}

    except Exception as e:
        print(f"[ERR] OCR Error: {e}")
        raise ValueError(f"Failed to extract text from image: {e}")


def extract_raw_text_from_image(image_path: str) -> str:
    """Extract ALL visible text from an image as plain text (no section structure)."""
    prompt = """You are an OCR system. Extract ALL text visible in this handwritten or printed image.

RULES:
- Output ONLY the raw text you see, nothing else
- Preserve line breaks and section headings exactly as written
- Include all labels, headings, and body text
- If any word is unclear, write your best guess inside [brackets]
- Do NOT add explanations, formatting, or commentary"""

    try:
        base64_image = encode_image_to_base64(image_path)
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ]
            }],
            extra_headers={"HTTP-Referer": YOUR_SITE_URL, "X-Title": YOUR_SITE_NAME},
            max_tokens=2048,
            temperature=0.1,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Raw text extraction error: {e}")
        return ""


def extract_multi_question_from_images(
    image_paths: list,
    question_configs: list
) -> dict:
    """
    Extract multi-question answers from scanned PDF page images.
    Each image = one PDF page. Combines all pages, splits by question, extracts sections.
    Returns: {1: {"Introduction": "...", ...}, 2: {...}, ...}
    """
    from app.services.pdf_processor import split_by_questions, extract_sections_from_text

    # Step 1: OCR every page to raw text
    all_text = ""
    for i, img_path in enumerate(image_paths):
        print(f"  OCR page {i+1}/{len(image_paths)}: {img_path}")
        page_text = extract_raw_text_from_image(img_path)
        all_text += f"\n--- Page {i+1} ---\n{page_text}"

    # Step 2: Split combined text by question boundaries
    q_chunks = split_by_questions(all_text, question_configs)

    # Step 3: Extract sections from each question chunk
    result = {}
    for cfg in question_configs:
        q_num = cfg["number"]
        section_names = [s["name"] for s in cfg["sections"]]
        chunk = q_chunks.get(q_num, "")
        result[q_num] = extract_sections_from_text(chunk, section_names)
        total = sum(len(v) for v in result[q_num].values())
        print(f"  Q{q_num}: {total} chars across {len(section_names)} sections")

    return result


# ── LLM-based section evaluation ─────────────────────────────────────────────

_STRICTNESS_GUIDE = {
    "lenient":  "Be generous. Award marks if the core concept is present, even with missing details. Give benefit of the doubt.",
    "moderate": "Be fair and balanced. Award partial marks for partially correct answers. Require key concepts to be present.",
    "strict":   "Be rigorous. Require precise technical terminology and complete concept coverage. Penalise vague or incomplete answers.",
}


def evaluate_section_with_llm(
    section_name: str,
    student_text: str,
    model_text: str,
    max_marks: float,
    strictness: str = "moderate",
    subject: str = "",
) -> dict:
    """
    Ask Gemini to evaluate one section of a student answer against the model answer.
    Returns {"marks_awarded": float, "reasoning": str, "concepts_covered": list, "concepts_missing": list}
    On any error returns {"marks_awarded": -1.0, ...} so caller knows to fall back to local scoring.
    """
    guide = _STRICTNESS_GUIDE.get(strictness, _STRICTNESS_GUIDE["moderate"])
    subject_line = f"Subject: {subject}\n" if subject else ""

    prompt = f"""You are an expert examiner evaluating one section of a student's written answer.

{subject_line}Section: {section_name}
Maximum marks for this section: {max_marks}

MODEL ANSWER (reference — what a correct answer looks like):
\"\"\"
{model_text}
\"\"\"

STUDENT ANSWER:
\"\"\"
{student_text}
\"\"\"

EVALUATION RULES:
- {guide}
- Award marks even if the student uses different words but demonstrates the correct concept
- Do NOT penalise concise writing — a short but conceptually correct answer can earn full marks
- Award 0 only if the answer is completely wrong, blank, or entirely off-topic
- marks_awarded must be a decimal between 0.0 and {max_marks}

Return ONLY valid JSON with no markdown or explanation:
{{
  "marks_awarded": <0.0 to {max_marks}>,
  "reasoning": "<one concise sentence explaining the marks>",
  "concepts_covered": ["<concept>"],
  "concepts_missing": ["<concept>"]
}}"""

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            extra_headers={"HTTP-Referer": YOUR_SITE_URL, "X-Title": YOUR_SITE_NAME},
            max_tokens=400,
            temperature=0.1,
        )
        text = response.choices[0].message.content.strip()
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            print(f"[WARN]  LLM evaluation: no JSON found for section '{section_name}'")
            return {"marks_awarded": -1.0, "reasoning": "parse_error", "concepts_covered": [], "concepts_missing": []}

        result = json.loads(match.group(0))
        result["marks_awarded"] = max(0.0, min(float(max_marks), float(result.get("marks_awarded", 0))))
        result.setdefault("concepts_covered", [])
        result.setdefault("concepts_missing", [])
        print(f"  LLM [{section_name}]: {result['marks_awarded']}/{max_marks} — {result.get('reasoning','')[:80]}")
        return result

    except Exception as e:
        print(f"[ERR] LLM section evaluation error ({section_name}): {e}")
        return {"marks_awarded": -1.0, "reasoning": str(e), "concepts_covered": [], "concepts_missing": []}