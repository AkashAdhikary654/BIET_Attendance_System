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

RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Stage 2: Runtime image
FROM python:3.10-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libopenblas0 \
    && rm -rf /var/lib/apt/lists/* /tmp/*

WORKDIR /app

COPY --from=builder /install /usr/local
COPY . .

ENV PORT=3000
EXPOSE 3000

CMD ["python", "app.py"]