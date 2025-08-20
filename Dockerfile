# Multi-stage Docker build for LangGraph Migration System
FROM python:3.11-slim as backend

# Set working directory
WORKDIR /app

# Install system dependencies for compilation
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements
COPY backend/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ .

# Expose port
EXPOSE 12001

# Command to run the application
CMD ["python", "api/server.py"]

# Frontend stage
FROM node:18-alpine as frontend

WORKDIR /app

# Copy package files
COPY frontend/package*.json ./

# Install dependencies
RUN npm ci --only=production

# Copy frontend code
COPY frontend/ .

# Build the app
RUN npm run build

# Production stage
FROM nginx:alpine as production

# Copy built frontend
COPY --from=frontend /app/build /usr/share/nginx/html

# Copy nginx config
COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]