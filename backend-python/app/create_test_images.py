"""
Generates two test images for AI evaluation testing:
  - test_model_answer.jpg   (the teacher's reference answer)
  - test_student_answer.jpg (a good student answer, ~70-80% expected score)

Topic: What is Deep Learning?
Run from: backend-python/app/
"""

from PIL import Image, ImageDraw, ImageFont
import os

# ── font helper ──────────────────────────────────────────────────────────────
def get_font(size=22):
    candidates = [
        "C:/Windows/Fonts/calibri.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/SEGOEUI.TTF",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            continue
    return ImageFont.load_default()

# ── image builder ─────────────────────────────────────────────────────────────
def make_image(lines, filename, width=1000):
    """
    lines: list of (text, bold) tuples
    Renders each line onto a white A4-ish image and saves as JPEG.
    """
    font_normal = get_font(22)
    font_bold   = get_font(26)
    font_title  = get_font(30)

    # Calculate height needed
    line_height = 38
    padding     = 60
    height      = padding * 2 + len(lines) * line_height + 20

    img  = Image.new("RGB", (width, height), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    # Light ruled lines (like notebook paper)
    for yy in range(padding, height - padding, line_height):
        draw.line([(40, yy + 30), (width - 40, yy + 30)], fill=(220, 220, 220), width=1)

    y = padding
    for text, style in lines:
        if style == "title":
            font = font_title
            color = (10, 60, 140)     # dark blue for headings
        elif style == "bold":
            font = font_bold
            color = (30, 30, 30)
        else:
            font = font_normal
            color = (40, 40, 40)

        draw.text((50, y), text, fill=color, font=font)
        y += line_height

    img.save(filename, "JPEG", quality=95)
    print(f"Created: {filename}")


# ═══════════════════════════════════════════════════════════════════════════════
#  MODEL ANSWER   (teacher's reference — comprehensive, full marks expected)
# ═══════════════════════════════════════════════════════════════════════════════
model_lines = [
    ("Question: What is Deep Learning? Explain its working and applications.", "title"),
    ("", "normal"),

    ("Definition:", "bold"),
    ("Deep Learning is a branch of Machine Learning that uses artificial neural", "normal"),
    ("networks with multiple layers (called deep neural networks) to automatically", "normal"),
    ("learn hierarchical representations from raw data without manual feature", "normal"),
    ("engineering. Each layer learns increasingly abstract features.", "normal"),
    ("", "normal"),

    ("Body:", "bold"),
    ("A deep learning network consists of an input layer, several hidden layers,", "normal"),
    ("and an output layer. Data flows forward through each layer (forward propagation),", "normal"),
    ("and the network adjusts its weights using backpropagation and gradient descent", "normal"),
    ("to minimize the loss function. Common architectures include:", "normal"),
    ("  - Convolutional Neural Networks (CNN): used for image classification.", "normal"),
    ("  - Recurrent Neural Networks (RNN / LSTM): used for sequential / time-series data.", "normal"),
    ("  - Transformers: used for natural language processing tasks.", "normal"),
    ("Training requires large labeled datasets and significant GPU compute power.", "normal"),
    ("Techniques like dropout, batch normalization, and data augmentation help", "normal"),
    ("prevent overfitting and improve generalization.", "normal"),
    ("", "normal"),

    ("Conclusion:", "bold"),
    ("Deep Learning has revolutionized Artificial Intelligence, achieving", "normal"),
    ("state-of-the-art results in computer vision, speech recognition,", "normal"),
    ("natural language processing, and autonomous systems. It is the core", "normal"),
    ("technology behind modern AI applications such as ChatGPT, Tesla Autopilot,", "normal"),
    ("medical image diagnosis, and real-time language translation.", "normal"),
]

# ═══════════════════════════════════════════════════════════════════════════════
#  STUDENT ANSWER  (good attempt — covers main points, ~70-80% expected)
# ═══════════════════════════════════════════════════════════════════════════════
student_lines = [
    ("Question: What is Deep Learning? Explain its working and applications.", "title"),
    ("", "normal"),

    ("Definition:", "bold"),
    ("Deep Learning is a type of Machine Learning that uses neural networks with", "normal"),
    ("many layers to learn patterns from data automatically. It does not require", "normal"),
    ("manual feature extraction because the network learns features on its own.", "normal"),
    ("", "normal"),

    ("Body:", "bold"),
    ("A deep learning model has an input layer, hidden layers, and an output layer.", "normal"),
    ("During training, data passes through each layer and the network updates its", "normal"),
    ("weights using backpropagation to reduce the error. Different types of deep", "normal"),
    ("learning networks are used for different tasks. CNN is used for images,", "normal"),
    ("RNN is used for text and sequences, and Transformers are used in NLP.", "normal"),
    ("Deep learning needs large amounts of data and GPUs to train well.", "normal"),
    ("", "normal"),

    ("Conclusion:", "bold"),
    ("Deep Learning is widely used in Artificial Intelligence today. It is used", "normal"),
    ("in image recognition, speech recognition, language translation, and", "normal"),
    ("self-driving cars. It has greatly improved the performance of AI systems", "normal"),
    ("compared to traditional machine learning methods.", "normal"),
]

# ── generate ──────────────────────────────────────────────────────────────────
output_dir = os.path.dirname(os.path.abspath(__file__))

make_image(model_lines,   os.path.join(output_dir, "test_model_answer.jpg"))
make_image(student_lines, os.path.join(output_dir, "test_student_answer.jpg"))

print()
print("Done! Use these files in the GRADX evaluation test:")
print("  Model Answer  -> test_model_answer.jpg")
print("  Student Sheet -> test_student_answer.jpg")
print("  Expected student score: ~70-80%")
