FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    jq \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy test files
COPY . .

# Set environment
ENV PYTHONPATH=/app
ENV PYTEST_TIMEOUT=300

CMD ["pytest", "tests/", "-v", "--tb=short", "--timeout=300"]