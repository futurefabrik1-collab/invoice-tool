# Multi-stage build for DigitalOcean

# Stage 1: Build frontend
FROM node:18-alpine AS frontend-builder

WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2: Python backend with built frontend
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-deu \
    libtesseract-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy Python requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ ./backend/
COPY data/ ./data/
COPY templates/ ./templates/
COPY signatures/ ./signatures/
COPY example-invoices/ ./example-invoices/

# Copy built frontend from stage 1
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Create output directory
RUN mkdir -p output

# Expose port
EXPOSE 8080

# Set environment variables
ENV FLASK_ENV=production
ENV PORT=8080

# Start with gunicorn
CMD gunicorn --bind 0.0.0.0:$PORT --workers 2 --timeout 120 backend.app:app
