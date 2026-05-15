# create_model_answer_image.py
from PIL import Image, ImageDraw, ImageFont

def create_model_answer_image():
    """Create a handwritten model answer image for AI"""
    
    model_text = """Definition: Artificial Intelligence is a branch of computer science that focuses on building systems capable of performing tasks that normally require human intelligence.

Body: Artificial Intelligence enables machines to learn from data and improve performance using techniques such as machine learning and deep learning. AI systems can be categorized into narrow AI, which performs specific tasks, and general AI, which aims to perform intellectual tasks similar to humans.

Conclusion: Artificial Intelligence is widely used in fields such as healthcare, education, transportation, business, and entertainment."""
    
    # Create image
    img = Image.new('RGB', (900, 450), color='white')
    draw = ImageDraw.Draw(img)
    
    try:
        font = ImageFont.truetype("arial.ttf", 18)
    except:
        font = ImageFont.load_default()
    
    y = 30
    for line in model_text.split('\n'):
        draw.text((30, y), line, fill='black', font=font)
        y += 30
    
    img.save("model_answer_image.jpg")
    print("✅ Created: model_answer_image.jpg")
    print("\n📝 Model answer image contains:")
    print(model_text)

if __name__ == "__main__":
    create_model_answer_image()