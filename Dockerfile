FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# System deps for faiss/llama-cpp etc - keep minimal, may need adjustments
RUN apt-get update && apt-get install -y build-essential libgcc1 git-lfs curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first for caching
COPY requirements.txt /app/requirements.txt
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy the rest
COPY . /app

# Create directories for model and data (mounted at runtime)
RUN mkdir -p /app/models && mkdir -p /app/data

EXPOSE 8000

CMD ["uvicorn", "src.app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
