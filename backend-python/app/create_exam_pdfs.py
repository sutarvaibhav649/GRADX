"""
Generate proper multi-question exam PDFs for GRADX testing.
Creates:
  exam_model_answer.pdf   — 4 questions, complete answers (model)
  exam_student_answer.pdf — 4 questions, partial answers (~62%)

Questions:
  Q1: Object-Oriented Programming       (8 marks)
  Q2: Database Normalization             (8 marks)
  Q3: OS Process Management             (8 marks)
  Q4: Computer Networks & OSI Model     (8 marks)
  TOTAL: 32 marks

Sections per question: Introduction, Core_Concepts, Examples, Conclusion

Run:
  python -m app.create_exam_pdfs
"""

import fitz
import textwrap
import os

# ─────────────────────────────────────────────────────────────────────────────
# Content
# ─────────────────────────────────────────────────────────────────────────────

MODEL = [
    {
        "number": 1,
        "title": "Object-Oriented Programming (OOP)",
        "sections": {
            "Introduction": (
                "Object-Oriented Programming (OOP) is a programming paradigm that organizes "
                "software design around objects and data, rather than functions and logic. An object "
                "is a self-contained unit that bundles both data (attributes) and behavior (methods). "
                "OOP was developed to make large software systems easier to manage, maintain, and scale. "
                "Languages like Java, C++, Python, and C# are built on OOP principles."
            ),
            "Core_Concepts": (
                "OOP is built on four fundamental principles. "
                "Encapsulation bundles data and methods inside a class and restricts direct access "
                "to internal state using access modifiers (private, protected, public), exposing only "
                "what is necessary. "
                "Inheritance allows a child class to acquire properties and methods from a parent class, "
                "enabling code reuse and hierarchical relationships. For example, a Dog class can "
                "inherit from an Animal class. "
                "Polymorphism allows the same method name to behave differently in different contexts, "
                "achieved through method overloading (compile-time) and method overriding (runtime). "
                "Abstraction hides complex implementation details and exposes only the essential "
                "interface, implemented using abstract classes and interfaces."
            ),
            "Examples": (
                "Consider a BankAccount class: it encapsulates balance and account number (private), "
                "exposes deposit() and withdraw() methods (public). A SavingsAccount can inherit from "
                "BankAccount and override calculateInterest() — this is both inheritance and polymorphism. "
                "In a vehicle system: Vehicle is the abstract base class; Car, Truck, Motorcycle inherit "
                "from it. Each overrides the move() method differently. A fleet management system can "
                "call move() on any vehicle without knowing its specific type — runtime polymorphism."
            ),
            "Conclusion": (
                "OOP provides a structured approach to software development that mirrors real-world "
                "entities. Its principles of encapsulation, inheritance, polymorphism, and abstraction "
                "reduce code duplication, improve maintainability, and allow teams to build modular, "
                "scalable applications. OOP is the dominant paradigm in enterprise and system software development."
            ),
        }
    },
    {
        "number": 2,
        "title": "Database Normalization",
        "sections": {
            "Introduction": (
                "Database normalization is the process of organizing a relational database to reduce "
                "data redundancy and improve data integrity. It involves decomposing tables into smaller, "
                "well-structured tables and defining relationships between them. Normalization follows a "
                "series of rules called Normal Forms (NF). The goal is to eliminate anomalies that occur "
                "during insert, update, and delete operations on unnormalized data."
            ),
            "Core_Concepts": (
                "First Normal Form (1NF) requires that each table cell contains a single (atomic) value "
                "and each record is unique — no repeating groups or arrays in columns. "
                "Second Normal Form (2NF) requires 1NF plus every non-key attribute must be fully "
                "functionally dependent on the entire primary key — eliminates partial dependencies, "
                "applicable when the key is composite. "
                "Third Normal Form (3NF) requires 2NF plus no transitive dependencies — a non-key "
                "attribute must not depend on another non-key attribute. "
                "Boyce-Codd Normal Form (BCNF) is a stricter version of 3NF where every determinant "
                "must be a candidate key. "
                "Fourth and Fifth Normal Forms address multi-valued and join dependencies respectively."
            ),
            "Examples": (
                "Consider a Student_Course table: (StudentID, CourseID, StudentName, CourseName, InstructorName). "
                "This violates 2NF because StudentName depends only on StudentID (partial dependency) "
                "and CourseName depends only on CourseID. "
                "Decompose into: Student(StudentID, StudentName), Course(CourseID, CourseName, InstructorID), "
                "Enrollment(StudentID, CourseID), Instructor(InstructorID, InstructorName). "
                "This eliminates update anomaly (changing a student name requires one update), "
                "insert anomaly (can add a course without enrollments), and delete anomaly."
            ),
            "Conclusion": (
                "Normalization is a systematic technique that ensures relational databases are free of "
                "redundancy and anomalies. While higher normal forms improve data integrity, they may "
                "require more joins in queries, sometimes causing denormalization for performance in "
                "read-heavy systems like data warehouses. Understanding normalization is fundamental "
                "to designing robust and efficient database schemas."
            ),
        }
    },
    {
        "number": 3,
        "title": "Operating System Process Management",
        "sections": {
            "Introduction": (
                "Process management is one of the core functions of an operating system. A process is "
                "an instance of a program in execution, consisting of the program code, current activity "
                "(program counter, registers), process stack, and heap. The OS manages multiple processes "
                "simultaneously, allocating CPU time, memory, and I/O resources while ensuring isolation "
                "and synchronization between concurrent processes."
            ),
            "Core_Concepts": (
                "A process passes through five states during its lifecycle: New (being created), Ready "
                "(waiting for CPU), Running (executing on CPU), Waiting/Blocked (waiting for I/O or event), "
                "and Terminated (finished execution). "
                "The Process Control Block (PCB) stores all information about a process: PID, state, "
                "program counter, CPU registers, memory limits, open file list, and scheduling information. "
                "CPU scheduling algorithms determine which ready process gets the CPU: "
                "FCFS (First Come First Served) — non-preemptive, simple but causes convoy effect; "
                "SJF (Shortest Job First) — optimal average waiting time but requires future knowledge; "
                "Round Robin — preemptive, time-quantum based, fair for interactive systems; "
                "Priority Scheduling — each process has a priority, risk of starvation solved by aging."
            ),
            "Examples": (
                "In Round Robin with quantum = 4ms: processes P1(24ms), P2(3ms), P3(3ms) execute in "
                "order P1(4), P2(3), P3(3), P1(4), P1(4), P1(4), P1(4), P1(4). "
                "Average waiting time = (6+4+7)/3 = 5.67ms. "
                "Context switching overhead: when the OS switches from P1 to P2, it saves P1's PCB "
                "(registers, program counter, stack pointer) and loads P2's PCB — this takes ~1-2 "
                "microseconds on modern hardware. "
                "Deadlock example: P1 holds Resource A and waits for B; P2 holds B and waits for A — "
                "circular wait. Prevented using Banker's Algorithm for safe state detection."
            ),
            "Conclusion": (
                "Effective process management is essential for system performance, responsiveness, and "
                "stability. The OS must balance CPU utilization, throughput, turnaround time, waiting "
                "time, and response time. Modern OS kernels use multilevel feedback queue schedulers "
                "that adapt to process behavior, and multicore systems further require parallel scheduling "
                "across multiple CPUs with cache affinity consideration."
            ),
        }
    },
    {
        "number": 4,
        "title": "Computer Networks and the OSI Model",
        "sections": {
            "Introduction": (
                "A computer network is a collection of interconnected devices that share resources and "
                "communicate using standardized protocols. Networks range from small Local Area Networks "
                "(LAN) to global Wide Area Networks (WAN) like the Internet. The OSI (Open Systems "
                "Interconnection) model, developed by ISO in 1984, provides a seven-layer conceptual "
                "framework that standardizes network communication functions, allowing interoperability "
                "between products from different vendors."
            ),
            "Core_Concepts": (
                "The OSI model has seven layers, each with distinct responsibilities: "
                "Layer 7 — Application: provides network services to end-user applications (HTTP, FTP, SMTP, DNS). "
                "Layer 6 — Presentation: data translation, encryption, compression (SSL/TLS, JPEG, ASCII). "
                "Layer 5 — Session: establishes, maintains, terminates sessions between applications. "
                "Layer 4 — Transport: end-to-end communication, segmentation, flow control, error recovery. "
                "TCP provides reliable, ordered delivery; UDP provides fast, connectionless delivery. "
                "Layer 3 — Network: logical addressing (IP), routing between networks using routers. "
                "Layer 2 — Data Link: framing, MAC addressing, error detection (Ethernet, Wi-Fi). "
                "Layer 1 — Physical: transmits raw bits over physical medium (cables, radio waves)."
            ),
            "Examples": (
                "When you access www.example.com: DNS (Application layer) resolves the domain to IP. "
                "Your browser creates an HTTP request (Application), TLS encrypts it (Presentation), "
                "TCP segments it with port 443 (Transport), IP adds source/destination addresses and "
                "routes through routers (Network), Ethernet frames carry it across the LAN with MAC "
                "addresses (Data Link), and electrical/optical signals physically transmit it (Physical). "
                "At the server, the process reverses — each layer strips its header and passes data up. "
                "TCP three-way handshake: SYN → SYN-ACK → ACK before data transfer."
            ),
            "Conclusion": (
                "The OSI model provides a universal framework for understanding and designing network "
                "communication. While the practical Internet uses the simpler TCP/IP model (4 layers), "
                "OSI remains the standard reference for troubleshooting and protocol design. Understanding "
                "how data encapsulation works across layers is fundamental to networking, cybersecurity, "
                "and distributed systems engineering."
            ),
        }
    },
]

# Student answers — partial, simpler, some sections weaker
STUDENT = [
    {
        "number": 1,
        "title": "Object-Oriented Programming (OOP)",
        "sections": {
            "Introduction": (
                "Object-Oriented Programming is a programming style that uses objects to organize code. "
                "Objects have data and methods. OOP makes programs easier to manage. "
                "Languages like Java, C++, and Python support OOP."
            ),
            "Core_Concepts": (
                "OOP has four main concepts. "
                "Encapsulation means hiding data inside a class using private variables and providing "
                "public methods to access them. "
                "Inheritance means a child class can use methods and properties from a parent class. "
                "This helps in reusing code. "
                "Polymorphism means the same method can behave differently in different classes. "
                "Abstraction hides complex details and shows only necessary information."
            ),
            "Examples": (
                "A Car class can inherit from Vehicle class. Car has its own start() method that "
                "overrides Vehicle's start(). This shows inheritance and polymorphism. "
                "BankAccount class keeps balance private and has deposit and withdraw methods."
            ),
            "Conclusion": (
                "OOP is useful for building large programs. It helps in code reuse and makes programs "
                "easier to understand. The four pillars make software development better."
            ),
        }
    },
    {
        "number": 2,
        "title": "Database Normalization",
        "sections": {
            "Introduction": (
                "Database normalization is the process of organizing database tables to reduce "
                "redundancy and dependency. It involves dividing tables into smaller tables. "
                "Normalization helps avoid problems when inserting, updating, or deleting data."
            ),
            "Core_Concepts": (
                "First Normal Form (1NF) means each column should have atomic values and no repeating groups. "
                "Second Normal Form (2NF) means the table should be in 1NF and all columns should "
                "depend on the full primary key. "
                "Third Normal Form (3NF) means no column should depend on a non-key column. "
                "These forms help make the database more organized."
            ),
            "Examples": (
                "A student table with StudentID, StudentName, CourseID, CourseName has redundancy "
                "because CourseName repeats. We can split it into Student table and Course table "
                "to remove this redundancy."
            ),
            "Conclusion": (
                "Normalization is important for good database design. It reduces redundancy and "
                "maintains data integrity. Higher normal forms give better structure to databases."
            ),
        }
    },
    {
        "number": 3,
        "title": "Operating System Process Management",
        "sections": {
            "Introduction": (
                "Process management is a function of the operating system that manages running programs. "
                "A process is a program that is currently running. The OS handles multiple processes "
                "at the same time by sharing CPU and memory resources."
            ),
            "Core_Concepts": (
                "A process has states: New, Ready, Running, Waiting, and Terminated. "
                "The OS uses a Process Control Block (PCB) to store information about each process "
                "like its ID, state, and registers. "
                "CPU scheduling decides which process runs next. "
                "FCFS runs processes in order of arrival. "
                "Round Robin gives each process a fixed time slice."
            ),
            "Examples": (
                "In Round Robin scheduling with quantum 4ms, processes take turns. "
                "If three processes P1, P2, P3 are ready, they each get 4ms turns repeatedly "
                "until they finish."
            ),
            "Conclusion": (
                "Process management ensures the CPU is used efficiently. Scheduling algorithms "
                "help balance performance and fairness. The OS must handle multiple processes "
                "running at the same time without conflicts."
            ),
        }
    },
    {
        "number": 4,
        "title": "Computer Networks and the OSI Model",
        "sections": {
            "Introduction": (
                "A computer network connects multiple computers so they can share data and resources. "
                "The OSI model is a standard model with seven layers that describes how data travels "
                "across a network from one device to another."
            ),
            "Core_Concepts": (
                "The OSI model has 7 layers. "
                "Application layer is the topmost layer used by applications like browsers. "
                "Transport layer uses TCP and UDP to send data reliably or quickly. "
                "Network layer handles IP addressing and routing using routers. "
                "Data Link layer handles MAC addresses and error detection. "
                "Physical layer transmits actual bits over cables or wireless signals."
            ),
            "Examples": (
                "When we open a website, the browser sends an HTTP request. TCP breaks it into "
                "segments, IP adds addresses, and it travels over the network to reach the server. "
                "The server sends back the webpage the same way."
            ),
            "Conclusion": (
                "The OSI model helps understand how networks work by dividing communication into "
                "layers. Each layer has a specific job. TCP/IP is the practical version used "
                "on the internet today."
            ),
        }
    },
]

# ─────────────────────────────────────────────────────────────────────────────
# PDF Builder
# ─────────────────────────────────────────────────────────────────────────────

# Colours
C_PRIMARY   = (0.10, 0.30, 0.60)   # dark blue
C_SECTION   = (0.55, 0.10, 0.10)   # dark red
C_WHITE     = (1.00, 1.00, 1.00)
C_BLACK     = (0.00, 0.00, 0.00)
C_LIGHT_BG  = (0.94, 0.96, 0.99)
C_BORDER    = (0.75, 0.80, 0.90)

PAGE_W, PAGE_H = 595, 842   # A4
MARGIN_L, MARGIN_R = 50, 50
MARGIN_T, MARGIN_B = 50, 50
TEXT_W = PAGE_W - MARGIN_L - MARGIN_R  # 495 pts
FONT  = "helv"
FONTB = "Helvetica-Bold"

# Character widths at fontsize 11 — estimate for word-wrap (conservative)
CHARS_PER_LINE = 88   # ~495pt / ~5.6pt per char at size 11


def wrap(text: str, width: int = CHARS_PER_LINE) -> list:
    """Wrap text to lines of `width` chars."""
    return textwrap.wrap(text, width=width, break_long_words=False, break_on_hyphens=True) or [""]


class PDFWriter:
    def __init__(self):
        self.doc  = fitz.open()
        self.page = None
        self.y    = MARGIN_T
        self._new_page()

    def _new_page(self):
        self.page = self.doc.new_page(width=PAGE_W, height=PAGE_H)
        self.y = MARGIN_T

    def _need_space(self, needed: float):
        if self.y + needed > PAGE_H - MARGIN_B:
            self._new_page()

    # ── primitive write ───────────────────────────────────────────────────────
    def _text(self, x, y, text, size=11, font=FONT, color=C_BLACK):
        self.page.insert_text(
            fitz.Point(x, y), text,
            fontname=font, fontsize=size, color=color
        )

    def _rect_fill(self, rect, fill, border=None):
        self.page.draw_rect(rect, color=border, fill=fill, width=0.8 if border else 0)

    # ── high-level elements ───────────────────────────────────────────────────
    def title_bar(self, title: str):
        """Full-width title bar at top of first page."""
        r = fitz.Rect(0, 0, PAGE_W, 52)
        self._rect_fill(r, fill=C_PRIMARY)
        self._text(MARGIN_L, 32, title, size=14, font=FONTB, color=C_WHITE)
        self.y = 68

    def question_header(self, number: int, title: str, total_marks: int):
        """Blue-background question block."""
        self._need_space(36)
        if self.y > MARGIN_T + 5:
            self.y += 10
        r = fitz.Rect(MARGIN_L - 8, self.y - 14, PAGE_W - MARGIN_R + 8, self.y + 16)
        self._rect_fill(r, fill=C_LIGHT_BG, border=C_BORDER)
        label = f"Question {number}:  {title}"
        marks = f"[{total_marks} marks]"
        self._text(MARGIN_L, self.y, label, size=12, font=FONTB, color=C_PRIMARY)
        # right-align marks
        self._text(PAGE_W - MARGIN_R - 55, self.y, marks, size=11, font=FONTB, color=C_PRIMARY)
        self.y += 24

    def section_header(self, name: str, marks: int):
        """Red section label."""
        self._need_space(24)
        self.y += 6
        display = name.replace("_", " ")
        label = f"{display}:  ({marks} marks)"
        self._text(MARGIN_L + 4, self.y, label, size=11, font=FONTB, color=C_SECTION)
        # underline
        tw = len(label) * 5.5   # rough width
        self.page.draw_line(
            fitz.Point(MARGIN_L + 4, self.y + 2),
            fitz.Point(MARGIN_L + 4 + tw, self.y + 2),
            color=C_SECTION, width=0.6
        )
        self.y += 16

    def body_text(self, text: str):
        """Wrapped body paragraph."""
        lines = wrap(text)
        for line in lines:
            self._need_space(16)
            self._text(MARGIN_L + 10, self.y, line, size=11, color=C_BLACK)
            self.y += 15
        self.y += 4   # paragraph gap

    def spacer(self, h: float = 12):
        self._need_space(h)
        self.y += h

    def save(self, path: str):
        self.doc.save(path)
        pages = len(self.doc)
        self.doc.close()
        print(f"  Saved: {path}  ({pages} page{'s' if pages != 1 else ''})")


# ─────────────────────────────────────────────────────────────────────────────
# Marks config (same for both PDFs — the structure is what matters)
# ─────────────────────────────────────────────────────────────────────────────

SECTION_MARKS = {
    "Introduction":   2,
    "Core_Concepts":  4,
    "Examples":       2,
    "Conclusion":     2,
}   # 10 marks per question × 4 questions = 40 marks total

QUESTION_TOTAL = sum(SECTION_MARKS.values())   # 10


def build_pdf(questions_data: list, path: str, title: str):
    w = PDFWriter()
    w.title_bar(title)
    for q in questions_data:
        w.question_header(q["number"], q["title"], QUESTION_TOTAL)
        for sec_name, marks in SECTION_MARKS.items():
            w.section_header(sec_name, marks)
            w.body_text(q["sections"][sec_name])
        w.spacer(16)
    w.save(path)


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    out = os.path.dirname(__file__)

    print("Generating exam PDFs...")
    build_pdf(MODEL,   os.path.join(out, "exam_model_answer.pdf"),
              "GRADX Exam — Model Answer  |  4 Questions  |  40 Marks")
    build_pdf(STUDENT, os.path.join(out, "exam_student_answer.pdf"),
              "GRADX Exam — Student Answer Sheet  |  Roll No: STU999")

    print()
    print("Configuration for GRADX exam creation:")
    print(f"  Questions: 4  |  Marks per question: {QUESTION_TOTAL}  |  Total: {4 * QUESTION_TOTAL}")
    print()
    for i in range(1, 5):
        topics = ["OOP", "Database Normalization", "OS Process Management", "Computer Networks"][i-1]
        print(f"  Q{i}: {topics}")
        for sec, m in SECTION_MARKS.items():
            print(f"       - {sec.replace('_',' ')}: {m} marks")
    print()
    print("Steps to test:")
    print("  1. Toggle Multi-Q (PDF) mode")
    print("  2. Add 4 questions with sections: Introduction(2), Core_Concepts(4), Examples(2), Conclusion(2)")
    print("  3. Upload exam_model_answer.pdf as model answer")
    print("  4. Upload exam_student_answer.pdf as student paper")
    print("  5. Max Marks = 40")
