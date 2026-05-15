# app/config.py
import os
from dotenv import load_dotenv

load_dotenv()

# OpenRouter configuration
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
if not OPENROUTER_API_KEY:
    raise ValueError("OPENROUTER_API_KEY environment variable is not set")

# Optional: GEMINI_API_KEY is no longer needed but keep for backward compatibility
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")  # Optional now