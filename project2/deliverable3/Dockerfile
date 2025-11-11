# Dockerfile
FROM python:3.11-slim

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy files
COPY . /app

# Install python deps
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Expose ports:
# 8501 - streamlit app
# 8000 - prometheus metrics
# 8080 - health
EXPOSE 8501 8000 8080

# Streamlit configuration (disable CORS for proxying and set server address)
ENV STREAMLIT_SERVER_ENABLECORS=false
ENV STREAMLIT_SERVER_HEADLESS=true
ENV PYTHONUNBUFFERED=1

# Entrypoint
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
