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

# Expose the port the app will listen on
EXPOSE 3000

# Launch through entrypoint.py which binds to the PORT env var
CMD ["python", "entrypoint.py"]