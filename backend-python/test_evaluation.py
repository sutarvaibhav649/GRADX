"""
GRADX Evaluation Test Script
Tests the hybrid LLM + local scoring with 5 student profiles:
  1. Excellent  — full coverage, well written
  2. Good       — most concepts, minor gaps
  3. Average    — partial coverage, vague
  4. Weak       — very little content
  5. Off-topic  — completely wrong answer
  6. No headers — correct answer but no section labels (tests fallback)

Run from backend-python/:
    $env:PYTHONUTF8="1"; python test_evaluation.py
"""

import os, sys, json, textwrap
from dotenv import load_dotenv

load_dotenv()

# -- Ask user which mode to run -------------------------------------------------
print("\n" + "="*70)
print("  GRADX EVALUATION TEST")
print("="*70)
print("\nMode options:")
print("  1 = LLM + Local hybrid  (accurate, calls Gemini API — costs tokens)")
print("  2 = Local only          (fast, free, no API calls)")
mode = (sys.argv[1] if len(sys.argv) > 1 else "1")
USE_LLM = (mode != "2")

# Monkey-patch evaluate_section_with_llm if running local-only
if not USE_LLM:
    import app.services.ocr_gemini as ocr_mod
    def _stub(*args, **kwargs):
        return {"marks_awarded": -1.0, "reasoning": "local-only mode", "concepts_covered": [], "concepts_missing": []}
    ocr_mod.evaluate_section_with_llm = _stub
    print("\n[LOCAL ONLY MODE — LLM calls disabled]\n")
else:
    print("\n[HYBRID MODE — Gemini LLM will be called for each section]\n")

from app.services.evaluator import AdvancedEvaluator

# ==============================================================================
# EXAM SETUP
# ==============================================================================
SUBJECT    = "Computer Science — Operating Systems"
STRICTNESS = "moderate"
TOPIC      = "Process Scheduling in Operating Systems"

MARKS_CONFIG = {
    "Definition":  2,
    "Types":       3,
    "Conclusion":  2,
}
MAX_MARKS = sum(MARKS_CONFIG.values())   # 7

MODEL_ANSWER = {
    "Definition": (
        "Process scheduling is the activity of the process manager that handles the removal "
        "of a running process from the CPU and selection of another process based on a "
        "particular strategy. It is a key function of multiprogramming operating systems "
        "that maximises CPU utilisation and ensures fair allocation of CPU time."
    ),
    "Types": (
        "The main scheduling algorithms are: "
        "1. First Come First Served (FCFS) — processes are scheduled in order of arrival; "
        "simple but causes the convoy effect. "
        "2. Shortest Job First (SJF) — selects the process with the smallest burst time; "
        "minimises average waiting time but requires knowledge of future burst times. "
        "3. Round Robin (RR) — each process is assigned a fixed time quantum in cyclic order; "
        "suitable for time-sharing systems. "
        "4. Priority Scheduling — each process is assigned a priority; CPU is given to the "
        "highest priority process; can cause starvation of low-priority processes. "
        "5. Multilevel Queue Scheduling — processes are permanently assigned to a queue "
        "based on properties like memory size or process type."
    ),
    "Conclusion": (
        "Process scheduling is fundamental to operating system design because it directly "
        "affects system performance, response time, and throughput. Choosing the right "
        "scheduling algorithm depends on the system requirements: FCFS for simplicity, "
        "SJF for minimum waiting time, and Round Robin for interactive systems."
    ),
}

# ==============================================================================
# STUDENT ANSWERS  (6 profiles)
# ==============================================================================
STUDENTS = [
    {
        "name": "Student A — Excellent",
        "answer": {
            "Definition": (
                "Process scheduling is the mechanism by which an operating system decides "
                "which process gets access to the CPU at any given time. It is essential in "
                "multiprogramming systems to maximise CPU utilisation and provide fair "
                "allocation of processing time among all running processes."
            ),
            "Types": (
                "There are several scheduling algorithms: "
                "FCFS (First Come First Served) schedules processes in arrival order — "
                "simple but can lead to the convoy effect. "
                "SJF (Shortest Job First) picks the process with the shortest burst time, "
                "minimising average waiting time but needing prior knowledge of burst times. "
                "Round Robin assigns a fixed time quantum to each process in rotation, "
                "ideal for time-sharing. "
                "Priority Scheduling runs the highest priority process first but may cause "
                "starvation. Multilevel Queue separates processes into queues by type."
            ),
            "Conclusion": (
                "Process scheduling is critical in OS design as it impacts CPU utilisation, "
                "throughput, and response time. The right algorithm depends on the use case: "
                "FCFS for batch systems, SJF for minimum waiting time, Round Robin for "
                "interactive and real-time environments."
            ),
        },
    },
    {
        "name": "Student B — Good",
        "answer": {
            "Definition": (
                "Process scheduling decides which process runs on the CPU. "
                "It is used in multiprogramming to keep the CPU busy and share processing "
                "time among processes fairly."
            ),
            "Types": (
                "FCFS — runs processes in order of arrival, simple but slow for long jobs. "
                "SJF — runs the shortest job first, gives minimum average waiting time. "
                "Round Robin — gives each process equal time in rotation, good for "
                "time-sharing systems. "
                "Priority Scheduling — runs highest priority first."
            ),
            "Conclusion": (
                "Scheduling is important for performance. Different algorithms suit different "
                "systems. Round Robin is best for interactive systems, SJF reduces wait time."
            ),
        },
    },
    {
        "name": "Student C — Average",
        "answer": {
            "Definition": (
                "Process scheduling is when the OS chooses which process to run. "
                "It helps use the CPU better."
            ),
            "Types": (
                "There are some types of scheduling like FCFS and Round Robin. "
                "FCFS means first come first served. Round Robin gives time to each process. "
                "There is also priority scheduling."
            ),
            "Conclusion": (
                "Scheduling is needed for the OS to work. It helps processes get CPU time."
            ),
        },
    },
    {
        "name": "Student D — Weak",
        "answer": {
            "Definition": "Scheduling is about processes in OS.",
            "Types":      "FCFS, SJF, Round Robin are some types.",
            "Conclusion": "It is important.",
        },
    },
    {
        "name": "Student E — Off-Topic / Wrong",
        "answer": {
            "Definition": (
                "RAM is a type of computer memory used to store data temporarily. "
                "It allows fast read and write access compared to hard disk storage."
            ),
            "Types": (
                "Types of RAM include DRAM, SRAM, and DDR. DRAM is used in main memory. "
                "SRAM is used in CPU caches because it is faster."
            ),
            "Conclusion": (
                "RAM is essential for computer performance. More RAM means the computer can "
                "run more applications at the same time."
            ),
        },
    },
    {
        "name": "Student F — No Section Headers (continuous writing)",
        "answer": {
            # Simulates: student wrote one continuous answer without labelling sections.
            # The fallback puts full text in every section.
            "Definition": (
                "Process scheduling is how the operating system decides which process uses "
                "the CPU. Multiprogramming needs this to utilise the CPU efficiently. "
                "Common scheduling algorithms include FCFS, SJF, Round Robin and Priority "
                "Scheduling. FCFS is simple but causes convoy effect. Round Robin is good "
                "for interactive systems as it gives equal time to all processes. "
                "SJF gives the shortest burst time process priority, reducing average waiting "
                "time. Scheduling is fundamental to OS design and affects throughput, response "
                "time and CPU utilisation."
            ),
            "Types": (
                "Process scheduling is how the operating system decides which process uses "
                "the CPU. Multiprogramming needs this to utilise the CPU efficiently. "
                "Common scheduling algorithms include FCFS, SJF, Round Robin and Priority "
                "Scheduling. FCFS is simple but causes convoy effect. Round Robin is good "
                "for interactive systems as it gives equal time to all processes. "
                "SJF gives the shortest burst time process priority, reducing average waiting "
                "time. Scheduling is fundamental to OS design and affects throughput, response "
                "time and CPU utilisation."
            ),
            "Conclusion": (
                "Process scheduling is how the operating system decides which process uses "
                "the CPU. Multiprogramming needs this to utilise the CPU efficiently. "
                "Common scheduling algorithms include FCFS, SJF, Round Robin and Priority "
                "Scheduling. FCFS is simple but causes convoy effect. Round Robin is good "
                "for interactive systems as it gives equal time to all processes. "
                "SJF gives the shortest burst time process priority, reducing average waiting "
                "time. Scheduling is fundamental to OS design and affects throughput, response "
                "time and CPU utilisation."
            ),
        },
    },
]

# ==============================================================================
# RUN EVALUATION
# ==============================================================================
print(f"Topic   : {TOPIC}")
print(f"Subject : {SUBJECT}")
print(f"Max     : {MAX_MARKS} marks  |  Sections: {list(MARKS_CONFIG.keys())}")
print(f"Mode    : {'Hybrid LLM+Local' if USE_LLM else 'Local only'}\n")
print("="*70)

results_summary = []

for student in STUDENTS:
    print(f"\n{'-'*70}")
    print(f"  Evaluating: {student['name']}")
    print(f"{'-'*70}")

    evaluator = AdvancedEvaluator()
    evaluator.auto_configure_from_model(
        {"Answer": MODEL_ANSWER, "topic": TOPIC},
        question_type="conceptual",
        cheating_threshold=0.4,
    )

    result = evaluator.evaluate(
        student["answer"],
        MODEL_ANSWER,
        MARKS_CONFIG,
        strictness=STRICTNESS,
        subject=SUBJECT,
    )

    total    = result["total_marks"]
    pct      = result["percentage"]
    feedback = result["feedback"]

    # Per-section breakdown
    for sec, data in result["section_scores"].items():
        llm_m   = data["scores"].get("llm_marks")
        local_m = data["scores"].get("local_marks", 0)
        sem     = data["scores"]["semantic_similarity"]
        cov     = data["scores"]["concept_coverage"]
        llm_str = f"LLM={llm_m:.1f}" if llm_m is not None else "LLM=fallback"

        llm_eval = data.get("llm_evaluation") or {}
        reasoning = llm_eval.get("reasoning", "")
        missing   = llm_eval.get("concepts_missing", [])

        print(f"\n  [{sec}]  {data['marks_awarded']}/{data['max_marks']} marks  "
              f"({data['percentage']}%)   {llm_str}  local={local_m:.1f}  "
              f"sem={sem:.2f}  cov={cov:.2f}")
        if reasoning:
            print(f"    Reason : {textwrap.shorten(reasoning, 80)}")
        if missing:
            print(f"    Missing: {', '.join(missing[:4])}")

    print(f"\n  TOTAL: {total}/{MAX_MARKS}  ({pct}%)")

    # Feedback summary
    if feedback["strengths"]:
        print(f"  Strengths   : {'; '.join(feedback['strengths'][:2])}")
    if feedback["improvements"]:
        print(f"  Improvements: {'; '.join(feedback['improvements'][:2])}")
    if feedback["warnings"]:
        print(f"  Warnings    : {'; '.join(feedback['warnings'])}")

    results_summary.append({
        "student": student["name"],
        "marks":   f"{total}/{MAX_MARKS}",
        "pct":     pct,
    })

# ==============================================================================
# SUMMARY TABLE
# ==============================================================================
print("\n\n" + "="*70)
print("  FINAL RESULTS SUMMARY")
print("="*70)
print(f"  {'Student':<40} {'Marks':>8}  {'%':>6}  Grade")
print(f"  {'-'*40}  {'-'*6}  {'-'*6}  -----")
for r in results_summary:
    p = r["pct"]
    grade = ("O" if p>=90 else "A+" if p>=80 else "A" if p>=70
             else "B+" if p>=60 else "B" if p>=50 else "C" if p>=40 else "F")
    print(f"  {r['student']:<40} {r['marks']:>8}  {p:>5.1f}%  {grade}")
print("="*70)
