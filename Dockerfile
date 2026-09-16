# Stage 1: Build dependencies
FROM python:3.10-slim AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    libopenblas-dev \
    liblapack-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /install

COPY requirements.txt .

# Compile wheels without saving cache to prevent running out of disk space
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Stage 2: Final lightweight runtime image
FROM python:3.10-slim

# Runtime libraries only (no compiler tools needed here)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libopenblas0 \
    && rm -rf /var/lib/apt/lists/* /tmp/*

WORKDIR /app

# Copy only installed Python packages from builder stage
COPY --from=builder /install /usr/local

COPY . .

ENV PORT=5000
EXPOSE 5000

CMD ["python", "app.py"]