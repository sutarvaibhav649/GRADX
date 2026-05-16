"""
Generates two biology test images:
  - biology_model_answer.jpg   (teacher reference — full marks)
  - biology_student_answer.jpg (~65-75% attempt)

Question: Describe the structure of an Animal Cell with a labeled diagram.
Sections:
  1. Introduction     (1 mark)
  2. Diagram          (2 marks)  ← ASCII-art labeled cell diagram
  3. Cell_Membrane    (1 mark)
  4. Nucleus          (1 mark)
  5. Cytoplasm        (1 mark)
  6. Conclusion       (1 mark)
  Total = 7 marks

Run from: backend-python/app/
"""

from PIL import Image, ImageDraw, ImageFont
import os

# ── font helper ───────────────────────────────────────────────────────────────
def get_font(size=20):
    candidates = [
        "C:/Windows/Fonts/calibri.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/SEGOEUI.TTF",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ]
    for p in candidates:
        try:
            return ImageFont.truetype(p, size)
        except Exception:
            continue
    return ImageFont.load_default()

def get_mono_font(size=18):
    candidates = [
        "C:/Windows/Fonts/cour.ttf",      # Courier New
        "C:/Windows/Fonts/consola.ttf",   # Consolas
        "C:/Windows/Fonts/lucon.ttf",     # Lucida Console
        "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
    ]
    for p in candidates:
        try:
            return ImageFont.truetype(p, size)
        except Exception:
            continue
    return get_font(size)

# ── image builder ─────────────────────────────────────────────────────────────
def make_image(lines, filename, width=1100):
    """
    lines: list of (text, style)
    style: 'title' | 'heading' | 'normal' | 'diagram'
    """
    font_normal  = get_font(20)
    font_heading = get_font(22)
    font_title   = get_font(26)
    font_diagram = get_mono_font(16)

    normal_lh  = 36
    diagram_lh = 24
    padding    = 60

    # Calculate total height
    total_h = padding
    for text, style in lines:
        total_h += diagram_lh if style == 'diagram' else normal_lh
    total_h += padding

    img  = Image.new("RGB", (width, total_h), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    # Light ruled lines
    for yy in range(padding, total_h - padding, normal_lh):
        draw.line([(40, yy + 28), (width - 40, yy + 28)], fill=(230, 230, 230), width=1)

    y = padding
    for text, style in lines:
        if style == "title":
            font, color, lh = font_title, (10, 60, 140), normal_lh
        elif style == "heading":
            font, color, lh = font_heading, (180, 50, 0), normal_lh
        elif style == "diagram":
            font, color, lh = font_diagram, (20, 100, 20), diagram_lh
        else:
            font, color, lh = font_normal, (40, 40, 40), normal_lh

        draw.text((50, y), text, fill=color, font=font)
        y += lh

    img.save(filename, "JPEG", quality=95)
    print(f"Created: {filename}")


# ═══════════════════════════════════════════════════════════════════════════════
#  MODEL ANSWER  — comprehensive, full 7 marks expected
# ═══════════════════════════════════════════════════════════════════════════════
model_lines = [
    ("Q: Describe the structure of an Animal Cell with a labeled diagram. (7 marks)", "title"),
    ("", "normal"),

    # ── Introduction (1 mark) ──────────────────────────────────────────────────
    ("Introduction:  [1 mark]", "heading"),
    ("An animal cell is the basic structural and functional unit of all animal organisms.", "normal"),
    ("It is a eukaryotic cell — it has a membrane-bound nucleus and membrane-bound organelles.", "normal"),
    ("Animal cells lack a cell wall, chloroplasts, and a large central vacuole.", "normal"),
    ("", "normal"),

    # ── Diagram (2 marks) ─────────────────────────────────────────────────────
    ("Diagram:  [2 marks]", "heading"),
    ("Labeled diagram of an Animal Cell:", "normal"),
    ("", "normal"),
    ("         Centriole                   Cell Membrane", "diagram"),
    ("             |                            |       ", "diagram"),
    ("             v                            v       ", "diagram"),
    ("      +------+--------[~Cell Membrane~]--------+", "diagram"),
    ("      |      |   *  *    *   *   *   *   *      |", "diagram"),
    ("      | [Cen]|  *  [Ribosome]  *    *    *   *  |", "diagram"),
    ("      |      | *   *   +-----------+  *    *     |", "diagram"),
    ("      |      |*  * *   | Nucleus   |   *  *   *  |", "diagram"),
    ("      |      |  *  *   | [Nucleolus|   *    *    |", "diagram"),
    ("      |  [ER]|    *    | inside]   |  [Mitochon] |", "diagram"),
    ("      |      |   *  *  +-----------+  *    *  *  |", "diagram"),
    ("      |      |  * [Golgi Body]  *   *    *       |", "diagram"),
    ("      +------+---[~~~~~~~~~~~~~~~~~~~~~~~~~]-----+", "diagram"),
    ("               ^            ^            ^        ", "diagram"),
    ("         Endoplasmic    Golgi Body   Mitochondria ", "diagram"),
    ("         Reticulum (ER)                           ", "diagram"),
    ("", "normal"),
    ("Labels: Cell Membrane, Nucleus, Nucleolus, Mitochondria,", "normal"),
    ("        Endoplasmic Reticulum, Golgi Body, Ribosome, Centriole.", "normal"),
    ("", "normal"),

    # ── Cell_Membrane (1 mark) ────────────────────────────────────────────────
    ("Cell_Membrane:  [1 mark]", "heading"),
    ("The cell membrane (plasma membrane) is a flexible phospholipid bilayer that", "normal"),
    ("surrounds the cell. It controls the movement of substances in and out of the", "normal"),
    ("cell (selective permeability). It also maintains cell shape and enables", "normal"),
    ("cell-to-cell communication via surface receptors.", "normal"),
    ("", "normal"),

    # ── Nucleus (1 mark) ──────────────────────────────────────────────────────
    ("Nucleus:  [1 mark]", "heading"),
    ("The nucleus is the control centre of the cell. It is enclosed by the nuclear", "normal"),
    ("envelope (double membrane with nuclear pores). It contains DNA in the form of", "normal"),
    ("chromosomes, which carry genetic information. The nucleolus inside the nucleus", "normal"),
    ("is responsible for producing ribosomes.", "normal"),
    ("", "normal"),

    # ── Cytoplasm (1 mark) ────────────────────────────────────────────────────
    ("Cytoplasm:  [1 mark]", "heading"),
    ("Cytoplasm is the jelly-like fluid (cytosol) that fills the cell between the", "normal"),
    ("cell membrane and the nucleus. It contains all organelles:", "normal"),
    ("  - Mitochondria: powerhouse of the cell; produces ATP via cellular respiration.", "normal"),
    ("  - Endoplasmic Reticulum (ER): rough ER has ribosomes for protein synthesis;", "normal"),
    ("    smooth ER is involved in lipid synthesis and detoxification.", "normal"),
    ("  - Golgi Body: packages and ships proteins and lipids to their destination.", "normal"),
    ("  - Ribosome: site of protein synthesis.", "normal"),
    ("  - Centriole: involved in cell division (forms spindle fibres).", "normal"),
    ("", "normal"),

    # ── Conclusion (1 mark) ───────────────────────────────────────────────────
    ("Conclusion:  [1 mark]", "heading"),
    ("The animal cell is a highly organised unit. Each organelle performs a specific", "normal"),
    ("function vital to the survival and proper functioning of the organism.", "normal"),
    ("Together, they carry out life processes such as energy production, protein", "normal"),
    ("synthesis, waste removal, and reproduction, making the cell the fundamental", "normal"),
    ("unit of life.", "normal"),
]

# ═══════════════════════════════════════════════════════════════════════════════
#  STUDENT ANSWER  — decent attempt, weak diagram labels, thin on cytoplasm
# ═══════════════════════════════════════════════════════════════════════════════
student_lines = [
    ("Q: Describe the structure of an Animal Cell with a labeled diagram. (7 marks)", "title"),
    ("", "normal"),

    # ── Introduction ──────────────────────────────────────────────────────────
    ("Introduction:", "heading"),
    ("An animal cell is the basic unit of life in animals. It is eukaryotic, meaning", "normal"),
    ("it has a nucleus. It does not have a cell wall like plant cells.", "normal"),
    ("", "normal"),

    # ── Diagram ───────────────────────────────────────────────────────────────
    ("Diagram:", "heading"),
    ("Labeled diagram of Animal Cell:", "normal"),
    ("", "normal"),
    ("      +---[Cell Membrane]---+", "diagram"),
    ("      |   *   *    *    *   |", "diagram"),
    ("      |  *  +----------+  * |", "diagram"),
    ("      |   * | Nucleus  | *  |", "diagram"),
    ("      |  *  +----------+  * |", "diagram"),
    ("      |   *  [Mitochondria] |", "diagram"),
    ("      |  *    *    *    *   |", "diagram"),
    ("      +--------------------+", "diagram"),
    ("", "normal"),
    ("Labels: Cell Membrane, Nucleus, Mitochondria.", "normal"),
    ("(Note: ER, Golgi Body, Ribosome, Centriole not labeled)", "normal"),
    ("", "normal"),

    # ── Cell_Membrane ─────────────────────────────────────────────────────────
    ("Cell_Membrane:", "heading"),
    ("The cell membrane surrounds the cell and controls what enters and leaves it.", "normal"),
    ("It is made of a phospholipid bilayer and is selectively permeable.", "normal"),
    ("", "normal"),

    # ── Nucleus ───────────────────────────────────────────────────────────────
    ("Nucleus:", "heading"),
    ("The nucleus is the control centre of the cell. It contains DNA and chromosomes.", "normal"),
    ("It is surrounded by the nuclear envelope.", "normal"),
    ("(Did not mention nucleolus or nuclear pores)", "normal"),
    ("", "normal"),

    # ── Cytoplasm ─────────────────────────────────────────────────────────────
    ("Cytoplasm:", "heading"),
    ("Cytoplasm is the fluid inside the cell. It contains the organelles.", "normal"),
    ("Mitochondria produce energy (ATP). Ribosomes make proteins.", "normal"),
    ("(No mention of ER, Golgi Body, or Centriole)", "normal"),
    ("", "normal"),

    # ── Conclusion ────────────────────────────────────────────────────────────
    ("Conclusion:", "heading"),
    ("The animal cell has many organelles that work together to keep the cell alive.", "normal"),
    ("Each part has its own function.", "normal"),
]

# ── generate ──────────────────────────────────────────────────────────────────
output_dir = os.path.dirname(os.path.abspath(__file__))

make_image(model_lines,   os.path.join(output_dir, "biology_model_answer.jpg"))
make_image(student_lines, os.path.join(output_dir, "biology_student_answer.jpg"))

print()
print("Done! Use these files in the GRADX evaluation test:")
print("  Model Answer   -> biology_model_answer.jpg")
print("  Student Answer -> biology_student_answer.jpg")
print("  Sections:")
print("    Introduction  (1 mark)")
print("    Diagram       (2 marks)")
print("    Cell_Membrane (1 mark)")
print("    Nucleus       (1 mark)")
print("    Cytoplasm     (1 mark)")
print("    Conclusion    (1 mark)")
print("  Total marks    -> 7")
print("  Expected score -> ~60-70%  (weak diagram + thin cytoplasm)")
