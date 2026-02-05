#!/bin/bash
set -e

# Change to script directory
cd "$(dirname "$0")"

echo "🚀 Starting Authentication Service..."

# Start Docker services
echo "📦 Starting Docker services (Redis + PostgreSQL)..."
docker compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 3

# Check Redis
echo "🔍 Checking Redis connection..."
until docker compose exec -T redis redis-cli ping 2>/dev/null | grep -q PONG; do
    echo "  Waiting for Redis..."
    sleep 1
done
echo "✅ Redis is ready"

# Check PostgreSQL
echo "🔍 Checking PostgreSQL connection..."
until docker compose exec -T postgres pg_isready -U user 2>/dev/null | grep -q "accepting connections"; do
    echo "  Waiting for PostgreSQL..."
    sleep 1
done
echo "✅ PostgreSQL is ready"

# Install dependencies if needed
if [ ! -d ".venv" ]; then
    echo "📚 Installing dependencies..."
    poetry install --no-root
else
    echo "✅ Dependencies already installed"
fi

# Run the server
echo "🎯 Starting FastAPI server on http://0.0.0.0:8000"
echo "📖 API Documentation: http://localhost:8000/docs"
echo ""
poetry run uvicorn main:app --reload --host 0.0.0.0 --port 8000
