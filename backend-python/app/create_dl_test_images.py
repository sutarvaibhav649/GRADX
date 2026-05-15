# create_dl_test_images.py
from PIL import Image, ImageDraw, ImageFont
import textwrap

def create_test_images():
    """Create test images for Deep Learning question"""
    
    # Excellent Answer
    excellent_answer = """Definition: Deep Learning is a subset of Machine Learning that uses neural networks with multiple layers to learn hierarchical representations of data.

Body: Deep Learning models, also known as deep neural networks, consist of input layers, hidden layers, and output layers. The multiple hidden layers automatically learn features from raw data without manual feature engineering. Each layer learns increasingly abstract representations.

Conclusion: Deep Learning powers modern AI applications like image recognition, natural language processing, and autonomous vehicles."""

    # Good Answer
    good_answer = """Definition: Deep Learning uses multi-layer neural networks to learn from data automatically.

Body: Deep Neural Networks have input, hidden, and output layers. The hidden layers learn features without manual engineering. This allows learning complex patterns.

Conclusion: Deep Learning is used for image recognition, NLP, and self-driving cars."""

    # Average Answer
    average_answer = """Definition: Deep Learning is a type of Machine Learning with many layers.

Body: It has input, hidden, and output layers. The network learns features from data.

Conclusion: Used in image recognition and language processing."""

    # Poor Answer
    poor_answer = """Definition: Deep Learning uses neural networks.

Body: It has layers and learns from data.

Conclusion: Used for AI."""

    # Keyword Stuffed Answer (Cheating)
    stuffed_answer = """Definition: deep learning machine learning neural networks multiple layers hierarchical representations

Body: deep neural networks input layers hidden layers output layers features manual feature engineering learning representations

Conclusion: image recognition natural language processing autonomous vehicles applications"""

    images = {
        "excellent_dl": excellent_answer,
        "good_dl": good_answer,
        "average_dl": average_answer,
        "poor_dl": poor_answer,
        "stuffed_dl": stuffed_answer
    }
    
    for name, text in images.items():
        # Calculate image height based on text length
        lines = text.split('\n')
        img_height = max(400, len(lines) * 35 + 50)
        img = Image.new('RGB', (900, img_height), color='white')
        draw = ImageDraw.Draw(img)
        
        y = 20
        for line in lines:
            wrapped_lines = textwrap.wrap(line, width=85)
            for wrapped in wrapped_lines:
                draw.text((20, y), wrapped, fill='black')
                y += 30
            y += 10
        
        img.save(f"{name}_q3.jpg")
        print(f"✅ Created: {name}_q3.jpg")
    
    print("\n📸 All test images created successfully!")

if __name__ == "__main__":
    create_test_images()