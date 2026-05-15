FROM python:3.11-slim

WORKDIR /app

# Set environment variables to reduce Python overhead
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install minimal system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for better caching)
COPY requirements.txt .

# Install only essential packages first
RUN pip install --no-cache-dir fastapi uvicorn[standard] python-multipart python-dotenv

# Install ML packages in separate layer (caches better)
RUN pip install --no-cache-dir \
    google-generativeai \
    pillow \
    numpy

# Install heavier packages last (rarely change)
RUN pip install --no-cache-dir \
    sentence-transformers \
    scikit-learn \
    nltk

# Download NLTK data
RUN python -c "import nltk; nltk.download('punkt', quiet=True); nltk.download('punkt_tab', quiet=True); nltk.download('stopwords', quiet=True)"

# Copy application code
COPY . .

# Create directory for evaluations
RUN mkdir -p evaluations

EXPOSE 8000

# Use direct command with host 0.0.0.0
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]