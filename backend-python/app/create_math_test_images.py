"""
Generates two math test images:
  - math_model_answer.jpg   (teacher's reference — full marks)
  - math_student_answer.jpg (good student attempt — ~70-80%)

Question: Solve the system of equations: 2x + y = 7 and x - y = 2
Sections : Given, Step1, Step2, Step3, Conclusion  (1 mark each = 5 marks)

Run from: backend-python/app/
"""

from PIL import Image, ImageDraw, ImageFont
import os

# ── font helper ───────────────────────────────────────────────────────────────
def get_font(size=22):
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

# ── image builder ─────────────────────────────────────────────────────────────
def make_image(lines, filename, width=1000):
    """
    lines: list of (text, style) where style is 'title' | 'heading' | 'normal'
    """
    font_normal  = get_font(22)
    font_heading = get_font(24)
    font_title   = get_font(28)

    line_height = 40
    padding     = 60
    height      = padding * 2 + len(lines) * line_height + 20

    img  = Image.new("RGB", (width, height), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    # Light ruled lines
    for yy in range(padding, height - padding, line_height):
        draw.line([(40, yy + 30), (width - 40, yy + 30)], fill=(220, 220, 220), width=1)

    y = padding
    for text, style in lines:
        if style == "title":
            font  = font_title
            color = (10, 60, 140)
        elif style == "heading":
            font  = font_heading
            color = (180, 50, 0)       # dark orange-red for section labels
        else:
            font  = font_normal
            color = (40, 40, 40)

        draw.text((50, y), text, fill=color, font=font)
        y += line_height

    img.save(filename, "JPEG", quality=95)
    print(f"Created: {filename}")


# ═══════════════════════════════════════════════════════════════════════════════
#  MODEL ANSWER  — comprehensive, full 5 marks expected
# ═══════════════════════════════════════════════════════════════════════════════
model_lines = [
    ("Q: Solve: 2x + y = 7  and  x - y = 2  (5 marks)", "title"),
    ("", "normal"),

    ("Given:", "heading"),
    ("Two simultaneous linear equations:", "normal"),
    ("    2x + y = 7   ... (1)", "normal"),
    ("    x  - y = 2   ... (2)", "normal"),
    ("We need to find the values of x and y.", "normal"),
    ("", "normal"),

    ("Step 1:", "heading"),
    ("Add equation (1) and equation (2) to eliminate y:", "normal"),
    ("    (2x + y) + (x - y) = 7 + 2", "normal"),
    ("    3x = 9", "normal"),
    ("    x = 3", "normal"),
    ("", "normal"),

    ("Step 2:", "heading"),
    ("Substitute x = 3 into equation (2):", "normal"),
    ("    3 - y = 2", "normal"),
    ("    y = 3 - 2", "normal"),
    ("    y = 1", "normal"),
    ("", "normal"),

    ("Step 3:", "heading"),
    ("Verification — substitute x = 3, y = 1 in both equations:", "normal"),
    ("    Eq (1): 2(3) + 1 = 6 + 1 = 7  [correct]", "normal"),
    ("    Eq (2): 3 - 1 = 2              [correct]", "normal"),
    ("Both equations are satisfied, so the solution is correct.", "normal"),
    ("", "normal"),

    ("Conclusion:", "heading"),
    ("The solution of the system of equations is:", "normal"),
    ("    x = 3   and   y = 1", "normal"),
]

# ═══════════════════════════════════════════════════════════════════════════════
#  STUDENT ANSWER  — good attempt, misses verification, ~70-80% expected
# ═══════════════════════════════════════════════════════════════════════════════
student_lines = [
    ("Q: Solve: 2x + y = 7  and  x - y = 2  (5 marks)", "title"),
    ("", "normal"),

    ("Given:", "heading"),
    ("Equations:  2x + y = 7  and  x - y = 2", "normal"),
    ("", "normal"),

    ("Step 1:", "heading"),
    ("Add both equations:", "normal"),
    ("    2x + y + x - y = 7 + 2", "normal"),
    ("    3x = 9  so  x = 3", "normal"),
    ("", "normal"),

    ("Step 2:", "heading"),
    ("Putting x = 3 in  x - y = 2:", "normal"),
    ("    3 - y = 2", "normal"),
    ("    y = 1", "normal"),
    ("", "normal"),

    ("Step 3:", "heading"),
    ("Checking in equation 1:  2(3) + 1 = 7  correct.", "normal"),
    ("(Did not check equation 2 separately)", "normal"),
    ("", "normal"),

    ("Conclusion:", "heading"),
    ("Therefore x = 3 and y = 1.", "normal"),
]

# ── generate ──────────────────────────────────────────────────────────────────
output_dir = os.path.dirname(os.path.abspath(__file__))

make_image(model_lines,   os.path.join(output_dir, "math_model_answer.jpg"))
make_image(student_lines, os.path.join(output_dir, "math_student_answer.jpg"))

print()
print("Done! Use these files in the GRADX evaluation test:")
print("  Model Answer   -> math_model_answer.jpg")
print("  Student Answer -> math_student_answer.jpg")
print("  Sections       -> Given (1), Step1 (1), Step2 (1), Step3 (1), Conclusion (1)")
print("  Total marks    -> 5")
print("  Expected score -> ~70-80%")
