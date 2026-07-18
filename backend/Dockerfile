FROM python:3.11-slim

# Install system dependencies (like git for cloning repos, and compile tools)
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend app code
COPY . .

# Set Python path to ensure imports resolve correctly
ENV PYTHONPATH=/workspace

EXPOSE 8000

# Default command runs the FastAPI app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
