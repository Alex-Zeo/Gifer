# Stage 1: Build stage with dependencies
FROM mcr.microsoft.com/playwright/python:v1.42.0-focal AS build

# Install FFmpeg
RUN apt-get update && apt-get install -y ffmpeg

WORKDIR /app

# Copy dependency files and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Stage 2: Final stage
FROM build AS final

WORKDIR /app

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
