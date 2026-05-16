"""
Create a simulated handwritten/scanned student answer PDF for GRADX testing.
The PDF contains ONLY embedded images (no text layer) → forces OCR path.

Run:  python -m app.create_scanned_pdf
"""

import fitz          # PyMuPDF  — to assemble images into PDF
from PIL import Image, ImageDraw, ImageFont
import io, os, textwrap

# ── Handwritten-style content (same 4 questions, slightly different wording) ──

CONTENT = [
    {
        "q": "Question 1:  Object-Oriented Programming (OOP)",
        "marks": "[10 marks]",
        "sections": [
            ("Introduction:  (2 marks)",
             "OOP stands for Object Oriented Programming. It is a way of writing programs\n"
             "using objects. An object has data and can do things (methods). Popular languages\n"
             "like Java and Python use OOP."),
            ("Core Concepts:  (4 marks)",
             "OOP has four pillars. Encapsulation keeps data private inside a class and gives\n"
             "public methods to access it. Inheritance lets a child class get properties from\n"
             "a parent class so we can reuse code. Polymorphism means the same method name can\n"
             "work differently in different classes. Abstraction hides details and shows only\n"
             "what is needed through interfaces or abstract classes."),
            ("Examples:  (2 marks)",
             "A Dog class can inherit from Animal class. Dog has its own speak() method that\n"
             "overrides Animal's speak(). A BankAccount class has private balance and public\n"
             "deposit() and withdraw() methods to encapsulate the data."),
            ("Conclusion:  (2 marks)",
             "OOP helps us write programs that are easier to manage. Code reuse through\n"
             "inheritance saves time. The four pillars make software modular and maintainable."),
        ],
    },
    {
        "q": "Question 2:  Database Normalization",
        "marks": "[10 marks]",
        "sections": [
            ("Introduction:  (2 marks)",
             "Database normalization organizes tables to reduce redundancy and improve\n"
             "integrity. It splits large tables into smaller related tables. This prevents\n"
             "problems during insert update and delete operations."),
            ("Core Concepts:  (4 marks)",
             "1NF means each cell has one value and no repeating groups. 2NF means we are\n"
             "in 1NF and every non-key column depends on the whole primary key. 3NF means\n"
             "no non-key column depends on another non-key column (no transitive dependency).\n"
             "BCNF is stronger than 3NF where every determinant is a candidate key."),
            ("Examples:  (2 marks)",
             "StudentCourse table with StudentID, StudentName, CourseID, CourseName. StudentName\n"
             "only depends on StudentID so this is a partial dependency violating 2NF. We split\n"
             "into Student(StudentID, StudentName) and Course(CourseID, CourseName)."),
            ("Conclusion:  (2 marks)",
             "Normalization makes databases clean and consistent. Higher normal forms reduce\n"
             "anomalies but may need more joins. It is essential for reliable database design."),
        ],
    },
    {
        "q": "Question 3:  Operating System Process Management",
        "marks": "[10 marks]",
        "sections": [
            ("Introduction:  (2 marks)",
             "Process management is done by the operating system. A process is a running\n"
             "program. The OS handles many processes together by sharing CPU memory and I/O\n"
             "resources between them."),
            ("Core Concepts:  (4 marks)",
             "Process states are New Ready Running Waiting and Terminated. The PCB (Process\n"
             "Control Block) stores the process state PID and registers. Scheduling algorithms\n"
             "choose which process runs. FCFS runs processes in arrival order. Round Robin\n"
             "gives each process a fixed time quantum. SJF picks shortest job first."),
            ("Examples:  (2 marks)",
             "Round Robin with quantum 4ms: P1 24ms P2 3ms P3 3ms. Order is P1(4) P2(3) P3(3)\n"
             "P1(4) P1(4) P1(4) P1(4) P1(4). Context switch saves and loads PCB data."),
            ("Conclusion:  (2 marks)",
             "Process management keeps the CPU busy and fair. Good scheduling improves\n"
             "response time and throughput. The OS must prevent deadlocks and starvation."),
        ],
    },
    {
        "q": "Question 4:  Computer Networks and the OSI Model",
        "marks": "[10 marks]",
        "sections": [
            ("Introduction:  (2 marks)",
             "A computer network connects devices so they can share data. The OSI model has\n"
             "7 layers and is a standard for how data travels across a network. It was made\n"
             "by ISO in 1984."),
            ("Core Concepts:  (4 marks)",
             "Layer 7 Application: HTTP FTP DNS for user apps. Layer 6 Presentation: encrypts\n"
             "and translates data. Layer 5 Session: manages sessions. Layer 4 Transport: TCP\n"
             "(reliable) and UDP (fast). Layer 3 Network: IP addresses and routing. Layer 2\n"
             "Data Link: MAC addresses and error detection. Layer 1 Physical: cables and bits."),
            ("Examples:  (2 marks)",
             "When opening a website: DNS resolves the name. Browser sends HTTP request.\n"
             "TCP segments it. IP routes it through routers. Ethernet carries it over LAN.\n"
             "TCP three-way handshake: SYN SYN-ACK ACK before data is sent."),
            ("Conclusion:  (2 marks)",
             "The OSI model is a reference model for networks. TCP/IP is the real 4-layer\n"
             "model used on the internet. Understanding layers helps in troubleshooting\n"
             "network problems and designing protocols."),
        ],
    },
]

# ── Page rendering ─────────────────────────────────────────────────────────────

PAGE_W, PAGE_H = 1240, 1754   # A4 at ~150 dpi
MARGIN_X, MARGIN_Y = 80, 80
LINE_H = 36
BG_COLOR   = (252, 250, 245)   # slight off-white (paper look)
TEXT_COLOR = (20, 20, 60)       # dark blue-black (pen ink)
Q_COLOR    = (10, 60, 140)      # blue heading
S_COLOR    = (140, 30, 10)      # red section label
RULE_COLOR = (200, 200, 200)    # light horizontal rule


def make_page(draw, y, q_data, is_first_q_on_page):
    """Render one question onto the image. Returns final y position."""

    # Question header
    if not is_first_q_on_page:
        y += 20
        draw.line([(MARGIN_X, y), (PAGE_W - MARGIN_X, y)], fill=RULE_COLOR, width=2)
        y += 20

    # Try to load a slightly bold-looking font; fall back to default
    try:
        font_q   = ImageFont.truetype("arial.ttf",  28)
        font_sec = ImageFont.truetype("ariali.ttf", 24)   # italic for sections
        font_body= ImageFont.truetype("arial.ttf",  22)
        font_marks = ImageFont.truetype("arial.ttf", 20)
    except Exception:
        font_q = font_sec = font_body = font_marks = ImageFont.load_default()

    draw.text((MARGIN_X, y), q_data["q"],    fill=Q_COLOR, font=font_q)
    y += LINE_H + 4
    draw.text((MARGIN_X + 4, y), q_data["marks"], fill=(100, 100, 100), font=font_marks)
    y += LINE_H + 8

    for sec_header, body in q_data["sections"]:
        # Section header
        y += 8
        draw.text((MARGIN_X, y), sec_header, fill=S_COLOR, font=font_sec)
        y += LINE_H

        # Body lines (word-wrapped)
        for line in body.splitlines():
            wrapped = textwrap.wrap(line, width=85)
            if not wrapped:
                y += LINE_H // 2
                continue
            for wline in wrapped:
                draw.text((MARGIN_X + 16, y), wline, fill=TEXT_COLOR, font=font_body)
                y += LINE_H
        y += 6

    return y


def render_pages(content):
    """Render all questions across as many pages as needed. Returns list of PIL Images."""
    pages = []
    img = Image.new("RGB", (PAGE_W, PAGE_H), BG_COLOR)
    draw = ImageDraw.Draw(img)
    y = MARGIN_Y

    # Title banner
    try:
        font_title = ImageFont.truetype("arial.ttf", 26)
    except Exception:
        font_title = ImageFont.load_default()
    banner_text = "GRADX  —  Student Answer Sheet (Handwritten Scan)   |   Roll: STU-SCAN-001"
    draw.rectangle([(0, 0), (PAGE_W, 60)], fill=(30, 60, 130))
    draw.text((30, 18), banner_text, fill=(255, 255, 255), font=font_title)
    y = 80

    for qi, q_data in enumerate(content):
        # Estimate height needed (~8 lines intro, core, examples, conclusion + headers)
        est_lines = 6 + sum(len(b.splitlines()) * 1.3 + 3 for _, b in q_data["sections"])
        est_height = int(est_lines * LINE_H) + 80

        if y + est_height > PAGE_H - MARGIN_Y and qi > 0:
            # Start new page
            pages.append(img)
            img = Image.new("RGB", (PAGE_W, PAGE_H), BG_COLOR)
            draw = ImageDraw.Draw(img)
            y = MARGIN_Y

        y = make_page(draw, y, q_data, y == MARGIN_Y)

    pages.append(img)
    return pages


def images_to_pdf(images, pdf_path):
    """Embed PIL images as pages in a PDF (no text layer → forces OCR)."""
    doc = fitz.open()
    for pil_img in images:
        # Convert PIL Image → bytes
        buf = io.BytesIO()
        pil_img.save(buf, format="JPEG", quality=92)
        buf.seek(0)
        img_bytes = buf.read()

        # Create a page and insert the image
        page = doc.new_page(width=pil_img.width * 0.75,   # scale to ~A4 pts
                            height=pil_img.height * 0.75)
        rect = fitz.Rect(0, 0, page.rect.width, page.rect.height)
        page.insert_image(rect, stream=img_bytes)

    doc.save(pdf_path)
    doc.close()
    print(f"Saved: {pdf_path}  ({len(images)} pages)")


if __name__ == "__main__":
    out_dir = os.path.dirname(__file__)
    out_path = os.path.join(out_dir, "scanned_student_answer.pdf")

    print("Rendering handwritten-style pages...")
    pages = render_pages(CONTENT)
    print(f"  {len(pages)} page(s) rendered")

    print("Assembling image-only PDF (no text layer)...")
    images_to_pdf(pages, out_path)

    # Verify: should have NO embedded text
    import fitz as _fitz
    doc = _fitz.open(out_path)
    total_chars = sum(len(p.get_text().strip()) for p in doc)
    doc.close()
    print(f"Embedded text chars (should be 0): {total_chars}")
    print(f"\nReady for OCR test: {out_path}")
