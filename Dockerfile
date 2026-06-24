# Stage 1: Build the React frontend
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend

# Copy package descriptors and lockfiles
COPY src/financial_planner/ui/frontend/package*.json ./
RUN npm ci

# Copy the rest of the frontend source code and compile
COPY src/financial_planner/ui/frontend/ ./
RUN npm run build

# Stage 2: Create the production container
FROM python:3.11-slim
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install python requirements
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source files and baseline data
COPY src/ /app/src/
COPY data/ /app/data/

# Copy the built static assets from frontend-builder stage into the location served by FastAPI
COPY --from=frontend-builder /app/frontend/dist /app/src/financial_planner/ui/frontend/dist

# Expose port (Cloud Run defaults to 8080 or sets the PORT environment variable)
ENV PORT=8080
EXPOSE 8080

# Run Uvicorn server in single-port mode (serving API and hosting UI static assets)
CMD ["sh", "-c", "python -m uvicorn src.financial_planner.api.main:app --host 0.0.0.0 --port ${PORT}"]
