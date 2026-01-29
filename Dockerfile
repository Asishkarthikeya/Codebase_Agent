FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create writable directories in /tmp (Hugging Face only allows writes to /tmp)
RUN mkdir -p /tmp/data /tmp/chroma_db /tmp/code_chatbot_extracted

# Expose Streamlit port
EXPOSE 7860

# Environment variables for Hugging Face Spaces
# Note: Actual API keys should be set in Hugging Face Space Secrets, not here
ENV STREAMLIT_SERVER_PORT=7860
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

# Run Streamlit
CMD ["streamlit", "run", "app.py", "--server.port=7860", "--server.address=0.0.0.0"]
