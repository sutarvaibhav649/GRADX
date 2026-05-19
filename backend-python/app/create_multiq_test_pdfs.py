"""
Generate multi-question test PDFs for GRADX PDF evaluation testing.
Creates:
  - multiq_model_answer.pdf  (strong, complete answers)
  - multiq_student_answer.pdf (partial answers, ~65-70% quality)

Run from backend-python/:
    python -m app.create_multiq_test_pdfs
"""

import fitz  # PyMuPDF

# ── Content definitions ───────────────────────────────────────────────────────

MODEL_ANSWER = """\
Question 1: What is Machine Learning?

Introduction:
Machine Learning is a subset of artificial intelligence that enables computers to learn
from data without being explicitly programmed. It involves algorithms that automatically
improve through experience and exposure to training data. ML builds mathematical models
based on sample data to make predictions or decisions without rule-based programming.

Types:
There are three main types of machine learning. Supervised Learning trains on labeled
data to map inputs to known outputs — used in classification and regression. Unsupervised
Learning finds hidden patterns in unlabeled data — used in clustering and dimensionality
reduction. Reinforcement Learning trains agents through reward and penalty signals to
maximize cumulative reward — used in robotics and game-playing systems.

Applications:
Machine learning is widely applied in image and speech recognition, natural language
processing, recommendation systems, medical diagnosis, fraud detection, and autonomous
vehicles. It powers voice assistants, spam filters, financial forecasting, and drug
discovery pipelines.

Conclusion:
Machine learning has fundamentally transformed computing by enabling systems to learn
from experience rather than explicit programming. Its ability to extract patterns from
large datasets makes it indispensable in modern technology across every industry.


Question 2: Explain Neural Networks

Introduction:
Neural networks are computational models inspired by the structure and function of the
human brain. They consist of layers of interconnected artificial neurons that process
information, learn feature representations, and produce outputs for complex tasks like
image recognition and natural language understanding.

Architecture:
A neural network is organized into three types of layers: an input layer that receives
raw data, one or more hidden layers that extract progressively abstract features, and an
output layer that produces the final prediction. Each neuron computes a weighted sum of
its inputs, adds a bias, and applies a non-linear activation function such as ReLU,
Sigmoid, or Tanh. Deep neural networks with many hidden layers are called deep learning
models.

Training:
Neural networks are trained using backpropagation combined with gradient descent
optimization. During the forward pass, data flows through the network to produce a
prediction. The loss function measures prediction error. Backpropagation computes the
gradient of the loss with respect to each weight using the chain rule. The optimizer
(SGD, Adam) then updates weights to minimize the loss over many training iterations.

Conclusion:
Neural networks are universal function approximators capable of learning arbitrarily
complex mappings from input to output. They form the backbone of modern deep learning
and have achieved state-of-the-art results in computer vision, NLP, speech recognition,
and generative AI applications.
"""

STUDENT_ANSWER = """\
Question 1: What is Machine Learning?

Introduction:
Machine Learning is a part of artificial intelligence that lets computers learn from
data without being programmed for every task. Algorithms improve automatically when
they are exposed to more training data.

Types:
Machine learning has three types. Supervised learning uses labeled training data to
make predictions. Unsupervised learning finds patterns in data without labels.
Reinforcement learning uses rewards to train an agent.

Applications:
ML is used in image recognition, recommendation systems, and fraud detection. It is
also used in natural language processing and speech recognition.

Conclusion:
Machine learning is an important field that helps computers learn from data. It has
many applications in technology and is growing rapidly.


Question 2: Explain Neural Networks

Introduction:
Neural networks are computing systems inspired by the human brain. They have
interconnected neurons in layers that process data and learn patterns.

Architecture:
A neural network has an input layer, hidden layers, and an output layer. Each neuron
uses an activation function and has weights connected to other neurons. Deep neural
networks have many hidden layers.

Training:
Neural networks are trained using backpropagation. The network makes predictions,
calculates error using a loss function, and updates weights using gradient descent.

Conclusion:
Neural networks can learn complex patterns from data. They are used in deep learning
for image recognition and language processing tasks.
"""

# ── PDF generation ────────────────────────────────────────────────────────────

def write_pdf(filename: str, text: str, title: str):
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)  # A4

    # Title banner
    page.draw_rect(fitz.Rect(0, 0, 595, 50), color=(0.15, 0.35, 0.65), fill=(0.15, 0.35, 0.65))
    page.insert_text((30, 32), title, fontsize=14, color=(1, 1, 1))

    margin_x = 50
    x = margin_x
    y = 70
    max_y = 800
    line_height = 16
    fontsize = 11

    for raw_line in text.splitlines():
        line = raw_line.rstrip()

        # New page if needed
        if y + line_height > max_y:
            page = doc.new_page(width=595, height=842)
            y = 50

        # Style: Question headers
        if line.startswith("Question "):
            if y > 70:
                y += 10  # extra space before question
            page.insert_text((x, y), line, fontsize=12, color=(0.15, 0.35, 0.65))
            # underline
            tw = fitz.get_text_length(line, fontsize=12)
            page.draw_line(fitz.Point(x, y + 2), fitz.Point(x + tw, y + 2),
                           color=(0.15, 0.35, 0.65), width=0.8)
            y += line_height + 4

        # Style: Section headers (word followed by colon at end)
        elif line and line.endswith(":") and len(line.split()) <= 3:
            y += 4
            page.insert_text((x, y), line, fontsize=11, color=(0.6, 0.15, 0.1))
            y += line_height

        # Empty line
        elif not line.strip():
            y += line_height // 2

        # Normal body text — word-wrap at ~75 chars
        else:
            words = line.split()
            cur = ""
            for word in words:
                test = (cur + " " + word).strip()
                if fitz.get_text_length(test, fontsize=fontsize) > 495:
                    if cur:
                        page.insert_text((x, y), cur, fontsize=fontsize, color=(0, 0, 0))
                        y += line_height
                        if y + line_height > max_y:
                            page = doc.new_page(width=595, height=842)
                            y = 50
                    cur = word
                else:
                    cur = test
            if cur:
                page.insert_text((x, y), cur, fontsize=fontsize, color=(0, 0, 0))
                y += line_height

    page_count = len(doc)
    doc.save(filename)
    doc.close()
    print(f"Created: {filename}  ({page_count} pages)")


if __name__ == "__main__":
    import os
    out_dir = os.path.dirname(__file__)

    model_path = os.path.join(out_dir, "multiq_model_answer.pdf")
    student_path = os.path.join(out_dir, "multiq_student_answer.pdf")

    write_pdf(model_path, MODEL_ANSWER, "GRADX — Model Answer (Multi-Question)")
    write_pdf(student_path, STUDENT_ANSWER, "GRADX — Student Answer (Multi-Question)")

    print("\nDone. Now test in GRADX:")
    print("  1. Toggle Multi-Q (PDF) mode in exam creation form")
    print("  2. Add Question 1: sections = Introduction(2), Types(3), Applications(2), Conclusion(1)")
    print("  3. Add Question 2: sections = Introduction(2), Architecture(3), Training(2), Conclusion(1)")
    print("  4. Upload multiq_model_answer.pdf as Model Answer")
    print("  5. Upload multiq_student_answer.pdf as Student Answer")
    print("  6. Max Marks will auto-sum to 16")
