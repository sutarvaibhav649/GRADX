# create_handwritten_images.py
from PIL import Image, ImageDraw, ImageFont
import random

def create_handwritten_image(text, filename, width=900, height=400):
    """Create an image that looks like handwritten text"""
    
    # Create white background image
    img = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(img)
    
    # Try to use a handwritten-style font if available
    try:
        # For Windows
        font_paths = [
            "C:/Windows/Fonts/SEGOEUI.TTF",
            "C:/Windows/Fonts/arial.ttf",
            "C:/Windows/Fonts/calibri.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",  # Linux
            "/System/Library/Fonts/Helvetica.ttc",  # Mac
        ]
        font = None
        for path in font_paths:
            try:
                font = ImageFont.truetype(path, 24)
                break
            except:
                continue
        if font is None:
            font = ImageFont.load_default()
    except:
        font = ImageFont.load_default()
    
    y = 30
    line_height = 35
    
    # Split text into lines
    lines = text.split('\n')
    
    for line in lines:
        # Add slight random offset for handwritten feel
        x = 30 + random.randint(-2, 2)
        
        # Draw each character with slight variation
        for char in line:
            draw.text((x, y), char, fill='black', font=font)
            x += 12 + random.randint(-1, 2)  # Variable spacing
        
        y += line_height + random.randint(-3, 3)
    
    img.save(filename)
    print(f"✅ Created: {filename}")

# Define test answers

# EXCELLENT ANSWER (Should get 7-8/8 marks)
excellent_answer = """Definition: Deep Learning is a subset of Machine Learning that uses neural networks with multiple layers to learn hierarchical representations of data.

Body: Deep Learning models, also known as deep neural networks, consist of input layers, hidden layers, and output layers. The hidden layers automatically learn features from raw data without manual feature engineering. Each layer learns increasingly abstract representations.

Conclusion: Deep Learning powers modern AI applications like image recognition, natural language processing, and autonomous vehicles."""

# GOOD ANSWER (Should get 5-6/8 marks)
good_answer = """Definition: Deep Learning is a subset of Machine Learning that uses neural networks with many layers.

Body: Deep Learning models have input, hidden, and output layers. They automatically learn features from data without manual engineering.

Conclusion: Deep Learning is used for image recognition, NLP, and self-driving cars."""

# AVERAGE ANSWER (Should get 3-4/8 marks)
average_answer = """Definition: Deep Learning is a type of Machine Learning with multiple neural network layers.

Body: It has input, hidden, and output layers. The network learns features from data.

Conclusion: Used in image recognition and language processing."""

# POOR ANSWER (Should get 1-2/8 marks)
poor_answer = """Definition: Deep Learning uses neural networks.

Body: It has layers and learns from data.

Conclusion: Used for AI."""

# KEYWORD STUFFED ANSWER (Cheating - Should get low marks with warning)
stuffed_answer = """Definition: deep learning machine learning neural networks multiple layers hierarchical representations

Body: deep neural networks input layers hidden layers output layers features raw data manual feature engineering

Conclusion: image recognition natural language processing autonomous vehicles"""

# Create all images
images = [
    (excellent_answer, "excellent_handwritten.jpg"),
    (good_answer, "good_handwritten.jpg"),
    (average_answer, "average_handwritten.jpg"),
    (poor_answer, "poor_handwritten.jpg"),
    (stuffed_answer, "stuffed_handwritten.jpg"),
]

print("📝 Creating handwritten-style test images...")
print("="*50)

for text, filename in images:
    create_handwritten_image(text, filename)

print("\n" + "="*50)
print("✅ All test images created successfully!")
print("\nFiles created:")
for _, filename in images:
    print(f"   - {filename}")