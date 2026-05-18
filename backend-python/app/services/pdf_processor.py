"""
PDF processing utilities for GRADX.
Typed PDFs → PyMuPDF direct text extraction (100% accurate, zero API cost).
Scanned PDFs → convert pages to images → OCR pipeline.
"""
import fitz  # PyMuPDF
import re
import tempfile
import os
from typing import Dict, List


# ── PDF type detection ────────────────────────────────────────────────────────

def is_text_based(pdf_path: str, min_chars_per_page: int = 50) -> bool:
    """Returns True if PDF has embedded text (typed/digital), False if scanned."""
    try:
        doc = fitz.open(pdf_path)
        total = sum(len(page.get_text().strip()) for page in doc)
        avg = total / max(1, len(doc))
        doc.close()
        return avg >= min_chars_per_page
    except Exception:
        return False


# ── Text extraction ───────────────────────────────────────────────────────────

def extract_full_text(pdf_path: str) -> str:
    """Extract all embedded text from a typed PDF. 100% accurate, zero API cost."""
    doc = fitz.open(pdf_path)
    pages = []
    for i, page in enumerate(doc):
        text = page.get_text()
        pages.append(f"--- Page {i+1} ---\n{text}")
    doc.close()
    return "\n".join(pages)


# ── Image conversion ──────────────────────────────────────────────────────────

def pdf_to_images(pdf_path: str, dpi: int = 200) -> List[str]:
    """Convert each PDF page to a temporary JPEG image. Returns list of temp paths."""
    doc = fitz.open(pdf_path)
    mat = fitz.Matrix(dpi / 72, dpi / 72)
    paths = []
    for i, page in enumerate(doc):
        pix = page.get_pixmap(matrix=mat)
        tmp = tempfile.mktemp(suffix=f"_page{i+1}.jpg")
        pix.save(tmp, jpg_quality=95)
        paths.append(tmp)
    doc.close()
    return paths


def cleanup_images(image_paths: List[str]):
    """Delete temporary image files."""
    for p in image_paths:
        try:
            if os.path.exists(p):
                os.unlink(p)
        except Exception:
            pass


# ── Question splitting ────────────────────────────────────────────────────────

_Q_RE = re.compile(
    r'(?:^|\n)\s*(?:'
    r'[Qq]uestion\s*(\d+)'              # "Question 1"
    r'|[Qq]ues(?:tion)?\.\s*(\d+)'     # "Ques. 1" or "Ques 1"
    r'|[Qq][\.\s]+(\d+)\s*[\.\):]'     # "Q.1:" or "Q 1."
    r'|[Qq](\d+)\s*[\.\):\-]'          # "Q1:" or "Q1-"
    r'|(\d+)\s*[\.\)]\s+'              # "1. " or "1) "
    r'|[Aa]ns(?:wer)?\s*\.?\s*(\d+)'   # "Ans 1", "Ans. 1", "Answer 1"
    r'|\((\d+)\)\s*'                    # "(1)"
    r')',
    re.MULTILINE
)


def split_by_questions(text: str, question_configs: List[Dict]) -> Dict[int, str]:
    """
    Split full PDF text into per-question chunks.
    question_configs: [{"number": 1, "sections": [...]}, ...]
    Returns: {1: "text for q1", 2: "text for q2", ...}
    """
    num_q = len(question_configs)
    matches = list(_Q_RE.finditer(text))

    if len(matches) >= num_q:
        chunks: Dict[int, str] = {}
        for idx, m in enumerate(matches[:num_q]):
            start = m.start()
            end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
            q_num = next((int(g) for g in m.groups() if g is not None), idx + 1)
            chunks[q_num] = text[start:end].strip()
        return chunks
    else:
        # No markers found — split text equally across questions
        n = max(1, num_q)
        size = max(1, len(text) // n)
        return {
            cfg["number"]: text[i * size: (i + 1) * size].strip()
            for i, cfg in enumerate(question_configs)
        }


# ── Section extraction from text ──────────────────────────────────────────────

def _norm(s: str) -> str:
    """Lowercase + collapse _/- to space for fuzzy section-name matching."""
    return re.sub(r'[_\-]+', ' ', s).lower().strip()


def _section_flex_re(name: str) -> str:
    """
    Regex fragment that matches a section name tolerantly:
    'Core_Concepts' matches 'Core Concepts', 'core-concepts', 'Core_Concepts'.
    Words are split on [_\\-\\s]+ and rejoined with [_\\-\\s]+.
    """
    parts = re.split(r'[_\-\s]+', name.strip())
    return r'[_\-\s]+'.join(re.escape(p) for p in parts if p)


def extract_sections_from_text(text_chunk: str, section_names: List[str]) -> Dict[str, str]:
    """
    Extract section-wise content from a question's text chunk.
    Handles underscore/hyphen/space variants: 'Core_Concepts' finds 'Core Concepts:'.
    Falls back to proportional distribution when no headers are found.
    """
    result = {s: "" for s in section_names}
    if not section_names or not text_chunk.strip():
        return result

    # Pattern matches any section header line (with optional trailing parens like "(4 marks)")
    combined = '|'.join(_section_flex_re(s) for s in section_names)
    pat = re.compile(
        r'(?:^|\n)\s*(?:' + combined + r')\s*[:\-]?\s*(?:\([^)]*\))?\s*(?=\n|$)',
        re.IGNORECASE
    )

    # Collect (section_name, match_start, body_start) for every matched header
    headers = []
    for m in pat.finditer(text_chunk):
        raw = m.group(0)
        # strip punctuation / parentheticals to get the bare name
        clean = re.sub(r'\s*\([^)]*\)', '', raw).strip().strip(':-').strip()
        for s in section_names:
            if _norm(clean) == _norm(s):
                headers.append((s, m.start(), m.end()))
                break

    # Extract body between consecutive headers
    # headers entries: (section_name, match_start, body_start)
    for idx, (sec, hdr_start, body_start) in enumerate(headers):
        body_end = headers[idx + 1][1] if idx + 1 < len(headers) else len(text_chunk)
        result[sec] = text_chunk[body_start:body_end].strip()

    # Fallback: student wrote a continuous answer with no section labels.
    # Put the full text into every section so semantic scoring can find relevant
    # content regardless of where the student placed it, instead of splitting
    # blindly by character count which puts random text in the wrong sections.
    if all(v == "" for v in result.values()) and text_chunk.strip():
        for s in section_names:
            result[s] = text_chunk.strip()

    return result


# ── Full structured extraction from typed PDF ─────────────────────────────────

def extract_multi_question_from_text(
    pdf_path: str,
    question_configs: List[Dict]
) -> Dict[int, Dict[str, str]]:
    """
    Extract all questions and sections from a typed PDF.
    Returns: {1: {"Introduction": "...", "Body": "..."}, 2: {...}, ...}
    100% accurate, zero API cost for typed PDFs.
    """
    full_text = extract_full_text(pdf_path)
    q_chunks = split_by_questions(full_text, question_configs)

    result: Dict[int, Dict[str, str]] = {}
    for cfg in question_configs:
        q_num = cfg["number"]
        sections = [s["name"] for s in cfg["sections"]]
        chunk = q_chunks.get(q_num, "")
        result[q_num] = extract_sections_from_text(chunk, sections)
        total_chars = sum(len(v) for v in result[q_num].values())
        print(f"  Q{q_num}: {total_chars} total chars extracted across {len(sections)} sections")

    return result
