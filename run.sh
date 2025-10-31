#!/bin/bash
set -e  # Exit on error

# Default host port
PORT=${1:-8080}
IMAGE_NAME="cancer-map-app"
CONTAINER_NAME="cancer-map-app"

echo "🔍 Checking Docker..."

# Check Docker is running
if ! docker info &> /dev/null; then
  echo "❌ Docker is not running. Please start Docker."
  exit 1
fi

# Stop existing container if running
echo "🧹 Cleaning up old container..."
docker stop $CONTAINER_NAME 2>/dev/null || true
docker rm $CONTAINER_NAME 2>/dev/null || true

# Check if port is in use
if lsof -i :$PORT &>/dev/null; then
  echo "⚠️ Port $PORT is in use. Trying $((PORT+1))..."
  PORT=$((PORT+1))
fi

echo "🔧 Building Docker image..."
if ! docker build -t $IMAGE_NAME .; then
  echo "❌ Build failed. Check logs above."
  exit 1
fi

echo "🚀 Starting app on http://localhost:$PORT ..."

# Create uploads directory if it doesn't exist
mkdir -p uploads

# Run container with volume mount to persist uploads
docker run -d \
  --name $CONTAINER_NAME \
  -p $PORT:5000 \
  -v "$(pwd)/uploads:/app/uploads" \
  --restart unless-stopped \
  $IMAGE_NAME

# Wait for app to be ready
echo "🕒 Waiting for app to start..."
for i in {1..30}; do
  if curl -s http://localhost:$PORT/ > /dev/null 2>&1; then
    echo "✅ App is live at: http://localhost:$PORT"
    echo "🛑 To stop: docker stop $CONTAINER_NAME"
    echo "📋 To view logs: docker logs -f $CONTAINER_NAME"
    exit 0
  fi
  sleep 1
done

echo "❌ App failed to start. Check logs: docker logs $CONTAINER_NAME"
exit 1