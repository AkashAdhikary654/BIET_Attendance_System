FROM python:3.10-slim

WORKDIR /app

# Ensure standard output and error are sent straight to logs (not buffered)
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=3000

# Install dependencies first for optimal Docker layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Expose all candidate ports so ECS / ALB port mapping matches any configured port
EXPOSE 3000 5000 8080 80

# Launch through entrypoint.py to bind to all candidate ports simultaneously
CMD ["python", "entrypoint.py"]