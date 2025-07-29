#!/bin/bash

echo "🚀 Starting Manufacturing RFQ Intelligence Platform..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Copy environment file if it doesn't exist
if [ ! -f .env ]; then
    echo "📋 Creating environment file..."
    cp .env.example .env
    echo "✅ Environment file created. Please review and update .env with your settings."
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p uploads
mkdir -p ml-models

# Start the services with Docker Compose
echo "🐳 Starting services with Docker Compose..."
docker-compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 10

# Check if services are running
echo "🔍 Checking service status..."
docker-compose ps

echo ""
echo "🎉 Manufacturing RFQ Platform is starting up!"
echo ""
echo "📊 Dashboard: http://localhost:3000"
echo "🔧 API Documentation: http://localhost:8000/docs"
echo "💾 Database: localhost:5432"
echo ""
echo "Default admin credentials:"
echo "Email: admin@rfq-platform.com"
echo "Password: admin123"
echo ""
echo "To stop the platform: docker-compose down"
echo "To view logs: docker-compose logs -f"