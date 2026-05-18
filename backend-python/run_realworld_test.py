"""
run_realworld_test.py  — Full evaluation pipeline test on 30 student PDFs.

Pre-requisite: run create_test_pdfs.py first to generate test_data/

Topic  : Artificial Intelligence
Sections: Definition(2) / Body(3) / Conclusion(2)  = 7 marks

API budget (free tier 200 req/day):
  - 15 typed   PDFs: 0 OCR (PyMuPDF) + 3 LLM eval each = 45 calls
  - 15 scanned PDFs: 1 OCR + 3 LLM eval = 4 calls each = 60 calls
  - 5 consistency re-runs                             = 15 calls
  Total ≈ 120 calls  (60% of daily limit)

Run from backend-python/:
    $env:PYTHONUTF8="1"; python run_realworld_test.py [--local-only]
"""

import os, sys, json, time, textwrap, pathlib, argparse
from datetime import datetime

# ── Load env FIRST so ocr_gemini client gets the API key at import time ──────
from dotenv import load_dotenv
load_dotenv()

# ── Parse args ──────────────────────────────────────────────────────────────
parser = argparse.ArgumentParser()
parser.add_argument("--local-only", action="store_true",
                    help="Disable LLM calls (local scoring only, zero API cost)")
args = parser.parse_args()

LOCAL_ONLY = args.local_only

# Monkey-patch LLM if running local-only
if LOCAL_ONLY:
    import app.services.ocr_gemini as _ocr_mod
    def _stub(*a, **kw):
        return {"marks_awarded": -1.0, "reasoning": "local-only mode",
                "concepts_covered": [], "concepts_missing": []}
    _ocr_mod.evaluate_section_with_llm = _stub
    print("\n[LOCAL ONLY — all LLM calls disabled, zero API cost]\n")
else:
    print("\n[HYBRID MODE — Gemini LLM will be called per section]\n")

from app.services.pdf_processor import (is_text_based, extract_full_text,
                                          pdf_to_images, cleanup_images,
                                          extract_sections_from_text)
from app.services.ocr_gemini    import extract_student_json
from app.services.evaluator     import AdvancedEvaluator

# ── Config ──────────────────────────────────────────────────────────────────
SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
DATA_DIR    = os.path.join(SCRIPT_DIR, "test_data")
TYPED_DIR   = os.path.join(DATA_DIR, "typed")
SCANNED_DIR = os.path.join(DATA_DIR, "scanned")
REPORT_DIR  = os.path.join(SCRIPT_DIR, "test_results")
os.makedirs(REPORT_DIR, exist_ok=True)

SUBJECT    = "Computer Science — Artificial Intelligence"
STRICTNESS = "moderate"
TOPIC      = "Artificial Intelligence"

MARKS_CONFIG = {"Definition": 2, "Body": 3, "Conclusion": 2}
MAX_MARKS    = sum(MARKS_CONFIG.values())  # 7

MODEL_ANSWER = {
    "Definition": (
        "Artificial Intelligence (AI) is the simulation of human intelligence processes by "
        "machines, especially computer systems. These processes include learning (the acquisition "
        "of information and rules for using it), reasoning (using rules to reach approximate or "
        "definite conclusions), and self-correction. AI enables machines to perform tasks that "
        "typically require human intelligence, such as visual perception, speech recognition, "
        "decision-making, and language translation."
    ),
    "Body": (
        "AI applications span multiple domains. Machine Learning (ML) is a subset of AI where "
        "systems learn from data without being explicitly programmed. Deep Learning uses neural "
        "networks with many layers to recognise patterns. Natural Language Processing (NLP) enables "
        "machines to understand and generate human language. Computer Vision allows machines to "
        "interpret visual information. Robotics integrates AI for autonomous physical actions. "
        "Key AI techniques include supervised learning, unsupervised learning, reinforcement "
        "learning, and transfer learning. AI is used in healthcare for diagnostics, in finance "
        "for fraud detection, in transportation for self-driving cars, and in education for "
        "personalised learning systems."
    ),
    "Conclusion": (
        "Artificial Intelligence represents a transformative technology that is reshaping "
        "industries and society. While AI offers immense benefits in automation, efficiency, "
        "and problem-solving, it also raises ethical concerns about privacy, bias, job "
        "displacement, and autonomous decision-making. Responsible AI development requires "
        "transparency, fairness, and accountability. The future of AI depends on advancing "
        "research in explainable AI, general AI, and quantum AI while ensuring human-centric "
        "design principles."
    ),
}

# Expected grade ordering (for accuracy measurement)
EXPECTED_ORDER = [
    "T01", "T02", "T03", "T04", "T05",  # should be highest
    "T06", "T07", "T08", "T10",          # mid range
    "T09", "T11", "T14",                  # lower
    "T12", "T13",                          # very low / zero
    "S16", "S19", "S22", "S24", "S25",   # scanned good
    "S17", "S20", "S23", "S26", "S27",   # scanned mid
    "S18", "S21", "S28", "S29", "S30",   # scanned weak
]

RATE_LIMIT_SEC = 2.5  # seconds between API-calling evaluations

# ── OCR helpers ─────────────────────────────────────────────────────────────

def ocr_pdf(pdf_path: str) -> dict:
    """
    Extract section dict from a student PDF.
    Typed → PyMuPDF (free).
    Scanned → Gemini OCR (1 API call per page).
    Returns {"Definition": "...", "Body": "...", "Conclusion": "..."}
    """
    section_names = list(MARKS_CONFIG.keys())

    if is_text_based(pdf_path):
        # Free path: PyMuPDF text extraction + section parsing
        raw_text = extract_full_text(pdf_path)
        sections = extract_sections_from_text(raw_text, section_names)
        return sections
    else:
        # Paid path: convert pages to images → Gemini OCR
        images = []
        try:
            images = pdf_to_images(pdf_path)
            if not images:
                return {s: "" for s in section_names}
            result = extract_student_json(images[0], section_names)
            return result.get("Answer", {s: "" for s in section_names})
        finally:
            cleanup_images(images)


# ── Evaluate one student ─────────────────────────────────────────────────────

def evaluate_student(pdf_path: str, student_id: str) -> dict:
    """Full pipeline: OCR → evaluate → return result dict."""
    t0 = time.time()

    # Step 1: OCR
    try:
        sections = ocr_pdf(pdf_path)
    except Exception as e:
        print(f"  [ERR] OCR failed for {student_id}: {e}")
        sections = {s: "" for s in MARKS_CONFIG}

    # Step 2: Evaluate
    evaluator = AdvancedEvaluator()
    evaluator.auto_configure_from_model(
        {"Answer": MODEL_ANSWER, "topic": TOPIC},
        question_type="conceptual",
        cheating_threshold=0.4,
    )
    result = evaluator.evaluate(
        sections,
        MODEL_ANSWER,
        MARKS_CONFIG,
        strictness=STRICTNESS,
        subject=SUBJECT,
    )

    elapsed = round(time.time() - t0, 1)
    result["_student_id"]       = student_id
    result["_pdf_path"]         = pdf_path
    result["_elapsed_sec"]      = elapsed
    result["_extracted_sections"] = sections
    return result


# ── Discover PDFs ────────────────────────────────────────────────────────────

def collect_pdfs():
    pdfs = []
    for f in sorted(pathlib.Path(TYPED_DIR).glob("student_*.pdf")):
        sid = f.stem.split("_")[1]
        pdfs.append({"id": sid, "path": str(f), "kind": "typed"})
    for f in sorted(pathlib.Path(SCANNED_DIR).glob("student_*.pdf")):
        sid = f.stem.split("_")[1]
        pdfs.append({"id": sid, "path": str(f), "kind": "scanned"})
    return pdfs


# ── Main test run ────────────────────────────────────────────────────────────

def main():
    pdfs = collect_pdfs()
    if not pdfs:
        print("[ERR] No PDFs found in test_data/typed/ or test_data/scanned/")
        print("      Run: python create_test_pdfs.py first")
        sys.exit(1)

    print("=" * 70)
    print(f"  GRADX Real-World Test  —  {len(pdfs)} student PDFs")
    print(f"  Topic   : {TOPIC}")
    print(f"  Max     : {MAX_MARKS} marks  |  Sections: {list(MARKS_CONFIG.keys())}")
    print(f"  Mode    : {'Local only' if LOCAL_ONLY else 'Hybrid LLM+Local'}")
    print("=" * 70)

    all_results = []
    typed_results   = []
    scanned_results = []

    for i, entry in enumerate(pdfs, 1):
        sid  = entry["id"]
        path = entry["path"]
        kind = entry["kind"]
        fname = os.path.basename(path)

        print(f"\n[{i:02d}/{len(pdfs)}] {fname}  ({kind})")
        result = evaluate_student(path, sid)
        result["_kind"] = kind

        total = result["total_marks"]
        pct   = result["percentage"]
        grade = ("O" if pct>=90 else "A+" if pct>=80 else "A" if pct>=70
                 else "B+" if pct>=60 else "B" if pct>=50 else "C" if pct>=40 else "F")
        result["_grade"] = grade

        print(f"  Marks: {total}/{MAX_MARKS}  ({pct}%)  Grade: {grade}  "
              f"[{result['_elapsed_sec']}s]")

        for sec, data in result["section_scores"].items():
            llm_m   = data["scores"].get("llm_marks")
            local_m = data["scores"].get("local_marks", 0)
            sem     = data["scores"]["semantic_similarity"]
            llm_str = f"LLM={llm_m:.1f}" if llm_m is not None else "LLM=skip"
            print(f"    [{sec:10s}] {data['marks_awarded']}/{data['max_marks']}  "
                  f"{llm_str}  local={local_m:.1f}  sem={sem:.2f}")

        # Rate limit only when LLM was called
        if not LOCAL_ONLY and i < len(pdfs):
            time.sleep(RATE_LIMIT_SEC)

        all_results.append(result)
        if kind == "typed":
            typed_results.append(result)
        else:
            scanned_results.append(result)

    # ── Consistency check (re-run 5 random PDFs) ────────────────────────────
    import random
    consistency_targets = random.sample(all_results, min(5, len(all_results)))
    consistency_diffs   = []

    print("\n" + "-"*70)
    print("  CONSISTENCY CHECK  (re-evaluating 5 random PDFs)")
    print("-"*70)
    for entry in consistency_targets:
        sid     = entry["_student_id"]
        path    = entry["_pdf_path"]
        marks1  = entry["total_marks"]
        result2 = evaluate_student(path, sid)
        marks2  = result2["total_marks"]
        diff    = abs(marks1 - marks2)
        consistency_diffs.append(diff)
        flag = "  <-- DRIFT" if diff > 0.5 else ""
        print(f"  {sid}: run1={marks1}/{MAX_MARKS}  run2={marks2}/{MAX_MARKS}  "
              f"diff={diff:.1f}{flag}")
        if not LOCAL_ONLY:
            time.sleep(RATE_LIMIT_SEC)

    avg_drift = round(sum(consistency_diffs) / len(consistency_diffs), 2) if consistency_diffs else 0.0

    # ── Generate stats report ────────────────────────────────────────────────
    print("\n\n" + "=" * 70)
    print("  FINAL RESULTS TABLE")
    print("=" * 70)
    print(f"  {'ID':<8} {'Kind':<8} {'Marks':>6}  {'%':>6}  Grade  Sem(avg)")
    print(f"  {'-'*8}  {'-'*8}  {'-'*5}  {'-'*5}  -----  --------")

    for r in all_results:
        sid   = r["_student_id"]
        kind  = r["_kind"]
        total = r["total_marks"]
        pct   = r["percentage"]
        grade = r["_grade"]
        avg_sem = round(
            sum(r["section_scores"][s]["scores"]["semantic_similarity"]
                for s in MARKS_CONFIG) / len(MARKS_CONFIG), 3
        )
        print(f"  {sid:<8} {kind:<8} {total:>5.1f}/{MAX_MARKS}  {pct:>5.1f}%  {grade:<5}  {avg_sem:.3f}")

    # ── Section-level stats ──────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("  SECTION DIFFICULTY ANALYSIS")
    print("=" * 70)
    for sec in MARKS_CONFIG:
        sec_pcts = [
            (r["section_scores"][sec]["marks_awarded"] / r["section_scores"][sec]["max_marks"]) * 100
            for r in all_results
        ]
        avg_pct = round(sum(sec_pcts) / len(sec_pcts), 1)
        min_pct = round(min(sec_pcts), 1)
        max_pct = round(max(sec_pcts), 1)
        print(f"  {sec:<12}: avg={avg_pct}%  min={min_pct}%  max={max_pct}%")

    # ── LLM vs Local correction ──────────────────────────────────────────────
    llm_corrections = []
    llm_skips       = 0
    for r in all_results:
        for sec, data in r["section_scores"].items():
            llm_m   = data["scores"].get("llm_marks")
            local_m = data["scores"].get("local_marks", 0)
            if llm_m is not None:
                llm_corrections.append(llm_m - local_m)
            else:
                llm_skips += 1

    print("\n" + "=" * 70)
    print("  LLM vs LOCAL SCORING")
    print("=" * 70)
    if llm_corrections:
        pos_corr = sum(1 for d in llm_corrections if d > 0.05)
        neg_corr = sum(1 for d in llm_corrections if d < -0.05)
        neu_corr = len(llm_corrections) - pos_corr - neg_corr
        avg_corr = round(sum(llm_corrections) / len(llm_corrections), 3)
        print(f"  Total scored sections : {len(llm_corrections)}")
        print(f"  LLM > local           : {pos_corr}  ({round(pos_corr/len(llm_corrections)*100)}%)")
        print(f"  LLM < local           : {neg_corr}  ({round(neg_corr/len(llm_corrections)*100)}%)")
        print(f"  LLM ~= local (<0.05)  : {neu_corr}  ({round(neu_corr/len(llm_corrections)*100)}%)")
        print(f"  Avg LLM correction    : {avg_corr:+.3f} marks")
    else:
        print("  (Local-only mode — LLM stats not available)")
    print(f"  LLM skipped (blank/OT) : {llm_skips}")

    # ── Typed vs Scanned comparison ──────────────────────────────────────────
    def avg_pct(results):
        return round(sum(r["percentage"] for r in results) / len(results), 1) if results else 0.0

    print("\n" + "=" * 70)
    print("  TYPED vs SCANNED COMPARISON")
    print("=" * 70)
    print(f"  Typed  ({len(typed_results):2d} PDFs): avg {avg_pct(typed_results)}%")
    print(f"  Scanned({len(scanned_results):2d} PDFs): avg {avg_pct(scanned_results)}%")

    # ── Grade distribution ───────────────────────────────────────────────────
    grade_counts = {}
    for r in all_results:
        g = r["_grade"]
        grade_counts[g] = grade_counts.get(g, 0) + 1

    print("\n" + "=" * 70)
    print("  GRADE DISTRIBUTION")
    print("=" * 70)
    for g in ["O", "A+", "A", "B+", "B", "C", "F"]:
        cnt = grade_counts.get(g, 0)
        bar = "#" * cnt
        print(f"  {g:<3}: {bar:<30} {cnt}")

    # ── Consistency ──────────────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("  CONSISTENCY ANALYSIS")
    print("=" * 70)
    print(f"  Re-run drift (avg): {avg_drift} marks  (target: < 0.3)")
    if avg_drift < 0.3:
        print("  [PASS] Evaluation is consistent")
    elif avg_drift < 0.7:
        print("  [WARN] Moderate drift — LLM temperature may need tuning")
    else:
        print("  [FAIL] High drift — evaluation is unstable")

    # ── Ordering accuracy ────────────────────────────────────────────────────
    id_to_pct = {r["_student_id"]: r["percentage"] for r in all_results}
    ranked    = sorted(id_to_pct.items(), key=lambda x: -x[1])
    ranked_ids = [x[0] for x in ranked]

    inversions = 0
    for i in range(len(EXPECTED_ORDER)):
        for j in range(i + 1, len(EXPECTED_ORDER)):
            a, b = EXPECTED_ORDER[i], EXPECTED_ORDER[j]
            if a in id_to_pct and b in id_to_pct:
                if id_to_pct[a] < id_to_pct[b]:
                    inversions += 1

    total_pairs = sum(1 for i in range(len(EXPECTED_ORDER))
                      for j in range(i+1, len(EXPECTED_ORDER))
                      if EXPECTED_ORDER[i] in id_to_pct and EXPECTED_ORDER[j] in id_to_pct)
    ordering_acc = round((1 - inversions / max(1, total_pairs)) * 100, 1)

    print("\n" + "=" * 70)
    print("  ORDERING ACCURACY")
    print("=" * 70)
    print(f"  Rank inversions vs expected : {inversions} / {total_pairs} pairs")
    print(f"  Ordering accuracy           : {ordering_acc}%  (target: > 80%)")
    if ordering_acc >= 80:
        print("  [PASS] Grade ordering is correct")
    elif ordering_acc >= 60:
        print("  [WARN] Partial ordering — some grades misordered")
    else:
        print("  [FAIL] Grade ordering is unreliable")

    # ── Save JSON report ─────────────────────────────────────────────────────
    report_path = os.path.join(
        REPORT_DIR,
        f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    )
    report = {
        "timestamp"        : datetime.now().isoformat(),
        "mode"             : "local-only" if LOCAL_ONLY else "hybrid-llm",
        "topic"            : TOPIC,
        "total_pdfs"       : len(all_results),
        "avg_pct_typed"    : avg_pct(typed_results),
        "avg_pct_scanned"  : avg_pct(scanned_results),
        "avg_drift"        : avg_drift,
        "ordering_accuracy": ordering_acc,
        "grade_distribution": grade_counts,
        "results"          : [
            {
                "id"         : r["_student_id"],
                "kind"       : r["_kind"],
                "marks"      : r["total_marks"],
                "max_marks"  : MAX_MARKS,
                "pct"        : r["percentage"],
                "grade"      : r["_grade"],
                "sections"   : {
                    sec: {
                        "awarded"  : r["section_scores"][sec]["marks_awarded"],
                        "max"      : r["section_scores"][sec]["max_marks"],
                        "sem_sim"  : r["section_scores"][sec]["scores"]["semantic_similarity"],
                        "llm_marks": r["section_scores"][sec]["scores"].get("llm_marks"),
                    }
                    for sec in MARKS_CONFIG
                },
            }
            for r in all_results
        ],
    }
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 70)
    print(f"  Report saved: {report_path}")
    print("=" * 70)


if __name__ == "__main__":
    main()
