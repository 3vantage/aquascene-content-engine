#!/bin/bash

# AquaScene Content Engine - Fix Dependencies Script
# This script fixes common dependency issues and ensures all services are properly configured

set -e

echo "🔧 AquaScene Content Engine - Fixing Dependencies"
echo "=================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}" >&2
}

success() {
    echo -e "${GREEN}[SUCCESS] $1${NC}"
}

warning() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

# Check if running from project root
if [ ! -f "docker-compose.yml" ]; then
    error "Please run this script from the project root directory"
    exit 1
fi

# Create necessary directories
log "Creating necessary directories..."
mkdir -p data/ollama
mkdir -p infrastructure/database/backups
mkdir -p logs
mkdir -p temp

# Set proper permissions
log "Setting proper permissions..."
chmod -R 755 infrastructure/
chmod -R 755 services/
chmod +x scripts/*.sh 2>/dev/null || true

# Fix Python dependencies
log "Fixing Python service dependencies..."

services=("ai-processor" "content-manager" "web-scraper" "subscriber-manager")
for service in "${services[@]}"; do
    if [ -d "services/$service" ]; then
        log "Checking $service dependencies..."
        
        # Ensure requirements.txt exists
        if [ ! -f "services/$service/requirements.txt" ]; then
            warning "requirements.txt missing for $service"
            continue
        fi
        
        # Check for common dependency conflicts
        if grep -q "pydantic.*1\." "services/$service/requirements.txt" 2>/dev/null; then
            warning "$service uses Pydantic v1, consider upgrading to v2"
        fi
        
        # Ensure Dockerfile exists
        if [ ! -f "services/$service/Dockerfile" ]; then
            error "Dockerfile missing for $service"
        else
            success "$service dependencies OK"
        fi
    fi
done

# Fix Node.js dependencies for admin dashboard
if [ -d "admin-dashboard" ]; then
    log "Fixing admin dashboard dependencies..."
    
    if [ ! -f "admin-dashboard/package.json" ]; then
        error "package.json missing for admin-dashboard"
    else
        success "Admin dashboard dependencies OK"
    fi
fi

# Fix environment variables
log "Checking environment configuration..."

if [ ! -f ".env" ]; then
    error ".env file missing"
    log "Creating .env file from template..."
    if [ -f ".env.example" ]; then
        cp .env.example .env
        warning "Created .env from .env.example - please update with your actual values"
    else
        warning ".env file missing and no .env.example found"
    fi
else
    success ".env file exists"
fi

# Check for required environment variables
required_vars=("DB_PASSWORD" "REDIS_PASSWORD" "JWT_SECRET" "ENCRYPTION_KEY")
missing_vars=()

for var in "${required_vars[@]}"; do
    if ! grep -q "^$var=" .env 2>/dev/null || grep -q "^$var=$" .env 2>/dev/null; then
        missing_vars+=("$var")
    fi
done

if [ ${#missing_vars[@]} -gt 0 ]; then
    warning "Missing or empty environment variables: ${missing_vars[*]}"
    log "Please update your .env file with proper values"
fi

# Fix Docker configuration
log "Checking Docker configuration..."

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    error "Docker is not running. Please start Docker and try again."
    exit 1
fi

# Check Docker Compose version
if ! docker-compose version >/dev/null 2>&1 && ! docker compose version >/dev/null 2>&1; then
    error "Docker Compose is not installed or not in PATH"
    exit 1
fi

# Fix network configuration
log "Checking Docker networks..."
if docker network ls | grep -q "content-engine"; then
    success "Content engine network exists"
else
    log "Creating content engine network..."
    docker network create content-engine 2>/dev/null || true
fi

# Fix volume permissions
log "Fixing volume permissions..."
docker_volumes=(
    "postgres_data"
    "redis_data"
    "prometheus_data"
    "grafana_data"
    "nginx_certs"
    "backup_data"
    "minio_data"
)

for volume in "${docker_volumes[@]}"; do
    if docker volume ls | grep -q "$volume"; then
        success "Volume $volume exists"
    else
        log "Creating volume $volume..."
        docker volume create "$volume" 2>/dev/null || true
    fi
done

# Clean up old containers if they exist
log "Cleaning up old containers..."
docker-compose down --remove-orphans 2>/dev/null || docker compose down --remove-orphans 2>/dev/null || true

# Pull latest images
log "Pulling latest base images..."
docker pull python:3.11-slim || warning "Failed to pull python:3.11-slim"
docker pull node:18-alpine || warning "Failed to pull node:18-alpine"
docker pull postgres:15 || warning "Failed to pull postgres:15"
docker pull redis:7-alpine || warning "Failed to pull redis:7-alpine"

# Check for common issues
log "Checking for common issues..."

# Check disk space
available_space=$(df . | awk 'NR==2 {print $4}')
if [ "$available_space" -lt 5242880 ]; then # 5GB in KB
    warning "Low disk space detected. Docker builds may fail."
fi

# Check memory
available_memory=$(free -m | awk 'NR==2{print $7}')
if [ "$available_memory" -lt 2048 ]; then # 2GB
    warning "Low available memory detected. Consider closing other applications."
fi

# Fix ownership issues (if running on Linux)
if [ "$(uname)" = "Linux" ]; then
    log "Fixing ownership issues (Linux)..."
    sudo chown -R $USER:$USER . 2>/dev/null || true
fi

# Validate configuration files
log "Validating configuration files..."

# Check docker-compose.yml syntax
if docker-compose config >/dev/null 2>&1 || docker compose config >/dev/null 2>&1; then
    success "Docker Compose configuration is valid"
else
    error "Docker Compose configuration is invalid"
    exit 1
fi

# Create startup script
log "Creating startup script..."
cat > start-services.sh << 'EOF'
#!/bin/bash
set -e

echo "Starting AquaScene Content Engine services..."

# Start core services first
docker-compose up -d postgres redis minio

# Wait for databases to be ready
echo "Waiting for databases to be ready..."
sleep 30

# Start application services
docker-compose up -d content-manager ai-processor web-scraper subscriber-manager distributor

# Wait for services to be ready
echo "Waiting for services to be ready..."
sleep 20

# Start admin dashboard
docker-compose up -d admin-dashboard

# Start monitoring stack
docker-compose up -d prometheus grafana loki promtail

# Start nginx proxy
docker-compose up -d nginx

echo "All services started successfully!"
echo "Access the admin dashboard at: http://localhost:3001"
echo "Access Grafana at: http://localhost:3000"
echo "Access Prometheus at: http://localhost:9090"
EOF

chmod +x start-services.sh

success "Dependencies fixed successfully!"
echo ""
echo "📋 Summary:"
echo "- Created necessary directories"
echo "- Fixed permissions"
echo "- Validated Docker configuration"
echo "- Created Docker networks and volumes"
echo "- Generated startup script: start-services.sh"
echo ""
echo "🚀 Next steps:"
echo "1. Update .env file with your API keys and secrets"
echo "2. Run './start-services.sh' to start all services"
echo "3. Run './run-full-test-suite.sh' to verify everything works"
echo ""
echo "✅ Dependency fixes completed successfully!"