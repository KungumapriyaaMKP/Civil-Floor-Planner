# Stage 1: Build React Frontend
FROM node:18-alpine as build
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# Stage 2: Helper for ffmpeg
# We need ffmpeg for stable audio
FROM python:3.10-slim

# Install system dependencies (ffmpeg)
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy Backend Code
COPY backend/ ./backend

# Copy Built Frontend from Stage 1
COPY --from=build /app/frontend/dist ./frontend/dist

# Expose Port (Hugging Face strict 7860)
EXPOSE 7860

# Command to run (Serve API + Static Files)
# We need to tweak main.py to serve static files first!
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "7860"]
