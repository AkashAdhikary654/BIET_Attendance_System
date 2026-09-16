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

# Expose the default application port
EXPOSE 3000

# Run with Gunicorn production server binding to dynamic $PORT or 3000
CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:${PORT:-3000} --workers 2 --threads 2 --timeout 120 app:app"]