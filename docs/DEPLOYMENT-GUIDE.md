# AquaScene Content Engine - Deployment Guide

**Version:** 1.0  
**Last Updated:** August 6, 2025  
**Environments:** Development, Staging, Production

## Overview

This guide provides step-by-step instructions for deploying the AquaScene Content Engine across different environments. The system uses Docker containers orchestrated with Docker Compose, with full monitoring and observability stack.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start Deployment](#quick-start-deployment)
3. [Environment-Specific Deployments](#environment-specific-deployments)
4. [Production Deployment](#production-deployment)
5. [Configuration Management](#configuration-management)
6. [Monitoring Setup](#monitoring-setup)
7. [Backup and Recovery](#backup-and-recovery)
8. [Security Configuration](#security-configuration)
9. [Troubleshooting](#troubleshooting)
10. [Maintenance](#maintenance)

## Prerequisites

### System Requirements

#### Minimum Hardware Requirements
```
CPU: 4 cores (2.0 GHz+)
Memory: 8 GB RAM
Storage: 50 GB available space
Network: Stable internet connection
```

#### Recommended Hardware Requirements
```
CPU: 8 cores (2.5 GHz+)
Memory: 16 GB RAM
Storage: 100 GB SSD
Network: High-speed internet connection
```

### Software Prerequisites

#### Required Software
```bash
# Docker Engine 20.10+
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Docker Compose 2.0+
# (Usually included with Docker Desktop)
# Or install standalone:
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Git 2.30+
sudo apt-get install git  # Ubuntu/Debian
brew install git          # macOS

# Optional: jq for JSON processing
sudo apt-get install jq   # Ubuntu/Debian
brew install jq           # macOS
```

#### System Configuration
```bash
# Increase Docker memory limits
# Add to /etc/docker/daemon.json
{
  "default-runtime": "runc",
  "runtimes": {
    "runc": {
      "path": "runc"
    }
  },
  "storage-driver": "overlay2",
  "storage-opts": [
    "overlay2.override_kernel_check=true"
  ],
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "100m",
    "max-file": "3"
  }
}

# Restart Docker
sudo systemctl restart docker
```

### API Keys and External Services

#### Required API Keys
```bash
# OpenAI (Required for premium AI features)
OPENAI_API_KEY="sk-your-openai-api-key"

# Anthropic (Required for Claude integration)
ANTHROPIC_API_KEY="sk-ant-your-anthropic-key"

# SendGrid (Required for email distribution)
SENDGRID_API_KEY="SG.your-sendgrid-key"

# Instagram (Optional, for social automation)
INSTAGRAM_ACCESS_TOKEN="your-instagram-token"
INSTAGRAM_PAGE_ID="your-page-id"
```

#### Optional Integrations
```bash
# Ollama (for local AI models)
OLLAMA_BASE_URL="http://localhost:11434"

# Airtable (for metadata management)
AIRTABLE_API_KEY="key-your-airtable-key"
AIRTABLE_BASE_ID="app-your-base-id"

# Google Gemini (alternative AI provider)
GEMINI_API_KEY="your-gemini-key"
```

## Quick Start Deployment

### 1. Clone and Setup

```bash
# Clone repository
git clone <repository-url>
cd aquascene-content-engine

# Make scripts executable
chmod +x *.sh

# Fix any dependency issues
./fix-dependencies.sh
```

### 2. Environment Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit configuration
nano .env  # or use your preferred editor

# Minimum required configuration:
DB_PASSWORD=your_secure_db_password
REDIS_PASSWORD=your_secure_redis_password
JWT_SECRET=your_jwt_secret_key
ENCRYPTION_KEY=your_32_byte_encryption_key
OPENAI_API_KEY=sk-your-openai-key
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key
```

### 3. Quick Start

```bash
# Start all services
./start-services.sh

# This script will:
# 1. Start core infrastructure (PostgreSQL, Redis, MinIO)
# 2. Wait for services to be ready
# 3. Start application services
# 4. Start monitoring stack
# 5. Start reverse proxy
```

### 4. Verification

```bash
# Check service status
docker-compose ps

# Run health checks
curl http://localhost:8000/health  # Content Manager
curl http://localhost:8001/health  # AI Processor

# Access web interfaces
open http://localhost:3001  # Admin Dashboard
open http://localhost:3000  # Grafana
open http://localhost:9090  # Prometheus

# Run full test suite
./run-full-test-suite.sh
```

## Environment-Specific Deployments

### Development Environment

#### Configuration
```bash
# Use development compose file
docker-compose -f docker-compose.yml -f docker-compose.override.yml up -d

# Development-specific settings in .env
DEBUG=true
LOG_LEVEL=DEBUG
CORS_ALLOW_ALL=true
ENABLE_DEBUG_ENDPOINTS=true
```

#### Features
- Hot reloading for code changes
- Debug endpoints enabled
- Verbose logging
- All services on localhost
- Development API keys

#### Commands
```bash
# Start development environment
docker-compose up -d

# View logs
docker-compose logs -f ai-processor

# Restart specific service
docker-compose restart content-manager

# Access database
docker-compose exec postgres psql -U postgres -d content_engine

# Access Redis
docker-compose exec redis redis-cli
```

### Staging Environment

#### Configuration
```bash
# Use staging compose file
docker-compose -f docker-compose.staging.yml up -d

# Staging-specific environment
cp .env.staging .env
```

#### Staging Environment File (.env.staging)
```bash
# Staging configuration
ENVIRONMENT=staging
DEBUG=false
LOG_LEVEL=INFO

# Database
DB_HOST=staging-postgres
DB_PORT=5432
DB_NAME=content_engine_staging

# External services (staging keys)
OPENAI_API_KEY=sk-staging-openai-key
ANTHROPIC_API_KEY=sk-ant-staging-anthropic-key
SENDGRID_API_KEY=SG.staging-sendgrid-key

# Monitoring
ENABLE_METRICS=true
ENABLE_ALERTING=true
```

#### Staging Deployment Steps
```bash
# 1. Setup staging environment
git checkout main
git pull origin main

# 2. Configure staging environment
cp .env.staging .env

# 3. Deploy staging services
docker-compose -f docker-compose.staging.yml up -d

# 4. Run staging tests
pytest services/e2e-testing/tests/ --env=staging

# 5. Performance testing
./test-performance.sh --env=staging

# 6. Validate deployment
./validate-deployment.sh --env=staging
```

## Production Deployment

### Pre-Deployment Checklist

```bash
# ✅ Prerequisites checklist
[ ] Hardware requirements met
[ ] All API keys configured
[ ] SSL certificates ready
[ ] Domain names configured
[ ] Backup strategy implemented
[ ] Monitoring alerts configured
[ ] Security review completed
[ ] Load testing completed
[ ] Disaster recovery plan ready
```

### Production Environment Setup

#### 1. Server Preparation
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Setup firewall
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw allow 9090/tcp  # Prometheus (internal)
sudo ufw allow 3000/tcp  # Grafana (internal)
sudo ufw enable

# Create application directory
sudo mkdir -p /opt/aquascene
sudo chown $USER:$USER /opt/aquascene
cd /opt/aquascene
```

#### 2. SSL Certificate Setup
```bash
# Using Let's Encrypt with Certbot
sudo apt install certbot

# Generate certificates
sudo certbot certonly --standalone \
  -d your-domain.com \
  -d api.your-domain.com \
  -d admin.your-domain.com

# Copy certificates to nginx directory
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem infrastructure/nginx/certs/
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem infrastructure/nginx/certs/
```

#### 3. Production Configuration

Create production environment file (.env.production):
```bash
# Production Environment Configuration
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO

# Database Configuration
DB_HOST=postgres
DB_PORT=5432
DB_NAME=content_engine_prod
DB_USER=postgres
DB_PASSWORD=your_super_secure_production_password

# Redis Configuration
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=your_super_secure_redis_password

# Security
JWT_SECRET=your_production_jwt_secret_minimum_32_chars
ENCRYPTION_KEY=your_32_byte_production_encryption_key

# AI Service APIs (Production Keys)
OPENAI_API_KEY=sk-prod-your-production-openai-key
ANTHROPIC_API_KEY=sk-ant-prod-your-production-anthropic-key

# Email Service
SENDGRID_API_KEY=SG.prod-your-production-sendgrid-key
FROM_EMAIL=noreply@your-domain.com
FROM_NAME=AquaScene Content Engine

# Instagram Integration
INSTAGRAM_ACCESS_TOKEN=your_production_instagram_token
INSTAGRAM_PAGE_ID=your_production_page_id

# Domain Configuration
DOMAIN=your-domain.com
API_DOMAIN=api.your-domain.com
ADMIN_DOMAIN=admin.your-domain.com

# SSL Configuration
SSL_CERTIFICATE_PATH=/etc/ssl/certs/your-domain.com/fullchain.pem
SSL_PRIVATE_KEY_PATH=/etc/ssl/certs/your-domain.com/privkey.pem

# Monitoring
ENABLE_METRICS=true
ENABLE_ALERTING=true
PROMETHEUS_RETENTION=30d
GRAFANA_SECURITY_ADMIN_PASSWORD=your_grafana_admin_password

# Performance Tuning
MAX_WORKERS=4
DB_POOL_SIZE=20
REDIS_POOL_SIZE=10
MAX_CONCURRENT_REQUESTS=50

# Backup Configuration
BACKUP_ENABLED=true
BACKUP_SCHEDULE="0 2 * * *"  # Daily at 2 AM
BACKUP_RETENTION_DAYS=30
BACKUP_S3_BUCKET=your-backup-bucket
BACKUP_S3_REGION=us-east-1
```

#### 4. Production Deployment

```bash
# Clone repository
git clone <repository-url> .
git checkout main

# Setup environment
cp .env.production .env

# Setup directories
mkdir -p {logs,data,backups}
chmod 755 {logs,data,backups}

# Deploy production stack
docker-compose -f docker-compose.production.yml up -d

# Wait for services to start
sleep 60

# Run production validation
./validate-production-deployment.sh
```

### Production Docker Compose Configuration

```yaml
# docker-compose.production.yml
version: '3.8'

networks:
  content-engine:
    driver: bridge
  monitoring:
    driver: bridge
  external:
    driver: bridge

volumes:
  postgres_data:
    driver: local
  redis_data:
    driver: local
  prometheus_data:
    driver: local
  grafana_data:
    driver: local
  minio_data:
    driver: local
  nginx_certs:
    driver: local
  backup_data:
    driver: local

services:
  # Core Database Services
  postgres:
    image: postgres:15
    container_name: content-engine-postgres-prod
    restart: always
    environment:
      POSTGRES_DB: ${DB_NAME}
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_MULTIPLE_DATABASES: ${DB_NAME},${DB_NAME}_test
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./infrastructure/database/init:/docker-entrypoint-initdb.d:ro
      - backup_data:/backups
    networks:
      - content-engine
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER} -d ${DB_NAME}"]
      interval: 30s
      timeout: 10s
      retries: 5
      start_period: 60s
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '1.0'

  redis:
    image: redis:7-alpine
    container_name: content-engine-redis-prod
    restart: always
    command: redis-server --requirepass ${REDIS_PASSWORD} --appendonly yes
    volumes:
      - redis_data:/data
      - ./infrastructure/redis/production.conf:/usr/local/etc/redis/redis.conf:ro
    networks:
      - content-engine
    healthcheck:
      test: ["CMD", "redis-cli", "--raw", "incr", "ping"]
      interval: 30s
      timeout: 10s
      retries: 5
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '0.5'

  # Application Services
  content-manager:
    image: aquascene/content-manager:${VERSION:-latest}
    container_name: content-manager-prod
    restart: always
    environment:
      - DATABASE_URL=postgresql://${DB_USER}:${DB_PASSWORD}@postgres:5432/${DB_NAME}
      - REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379
      - JWT_SECRET=${JWT_SECRET}
      - ENVIRONMENT=production
      - LOG_LEVEL=INFO
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - content-engine
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '1.0'
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3

  ai-processor:
    image: aquascene/ai-processor:${VERSION:-latest}
    container_name: ai-processor-prod
    restart: always
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - DATABASE_URL=postgresql://${DB_USER}:${DB_PASSWORD}@postgres:5432/${DB_NAME}
      - REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379
      - ENVIRONMENT=production
      - LOG_LEVEL=INFO
      - MAX_CONCURRENT_REQUESTS=${MAX_CONCURRENT_REQUESTS:-20}
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - content-engine
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '2.0'
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3

  # Reverse Proxy
  nginx:
    image: nginx:alpine
    container_name: content-engine-nginx-prod
    restart: always
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./infrastructure/nginx/production.conf:/etc/nginx/nginx.conf:ro
      - ./infrastructure/nginx/ssl.conf:/etc/nginx/conf.d/ssl.conf:ro
      - nginx_certs:/etc/ssl/certs:ro
      - ./infrastructure/nginx/html:/usr/share/nginx/html:ro
    depends_on:
      - content-manager
      - ai-processor
    networks:
      - content-engine
      - external
    deploy:
      resources:
        limits:
          memory: 256M
          cpus: '0.5'

  # Monitoring Stack
  prometheus:
    image: prom/prometheus:latest
    container_name: content-engine-prometheus-prod
    restart: always
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--storage.tsdb.retention.time=${PROMETHEUS_RETENTION:-30d}'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
      - '--web.enable-lifecycle'
    volumes:
      - ./infrastructure/monitoring/prometheus/production.yml:/etc/prometheus/prometheus.yml:ro
      - prometheus_data:/prometheus
    networks:
      - monitoring
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '1.0'

  grafana:
    image: grafana/grafana:latest
    container_name: content-engine-grafana-prod
    restart: always
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_SECURITY_ADMIN_PASSWORD}
      - GF_INSTALL_PLUGINS=grafana-piechart-panel
    volumes:
      - grafana_data:/var/lib/grafana
      - ./infrastructure/monitoring/grafana/provisioning:/etc/grafana/provisioning:ro
      - ./infrastructure/monitoring/grafana/dashboards:/var/lib/grafana/dashboards:ro
    depends_on:
      - prometheus
    networks:
      - monitoring
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '0.5'
```

## Configuration Management

### Environment Variables

#### Core Configuration
```bash
# Service Configuration
SERVICE_NAME=aquascene-content-engine
VERSION=1.0.0
ENVIRONMENT=production  # development, staging, production

# Network Configuration
HOST=0.0.0.0
PORT=8000

# Database Configuration
DB_HOST=postgres
DB_PORT=5432
DB_NAME=content_engine
DB_USER=postgres
DB_PASSWORD=your_secure_password
DATABASE_URL=postgresql://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}

# Redis Configuration
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=your_redis_password
REDIS_URL=redis://:${REDIS_PASSWORD}@${REDIS_HOST}:${REDIS_PORT}
```

#### Security Configuration
```bash
# Authentication & Security
JWT_SECRET=your_jwt_secret_key_minimum_32_characters
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24
ENCRYPTION_KEY=your_32_byte_encryption_key
BCRYPT_ROUNDS=12

# CORS Configuration
CORS_ALLOW_ORIGINS=https://your-domain.com,https://admin.your-domain.com
CORS_ALLOW_CREDENTIALS=true
CORS_ALLOW_METHODS=GET,POST,PUT,DELETE,OPTIONS
CORS_ALLOW_HEADERS=*
```

#### AI Service Configuration
```bash
# OpenAI Configuration
OPENAI_API_KEY=sk-your-openai-api-key
OPENAI_MODEL=gpt-4
OPENAI_MAX_TOKENS=2000
OPENAI_TEMPERATURE=0.7

# Anthropic Configuration
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key
ANTHROPIC_MODEL=claude-3-opus-20240229
ANTHROPIC_MAX_TOKENS=2000

# Ollama Configuration (Optional)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODELS=llama3.1:8b,mistral:7b

# AI Service Settings
DEFAULT_LLM_PROVIDER=openai
LLM_TIMEOUT_SECONDS=30
MAX_RETRIES=3
ENABLE_LLM_CACHING=true
LLM_CACHE_TTL_SECONDS=3600
```

### Configuration Validation

#### Validation Script
```bash
#!/bin/bash
# validate-config.sh

set -e

echo "🔍 Validating AquaScene Content Engine Configuration"
echo "=================================================="

# Load environment variables
if [ -f .env ]; then
    source .env
else
    echo "❌ .env file not found"
    exit 1
fi

# Required variables
required_vars=(
    "DB_PASSWORD"
    "REDIS_PASSWORD"
    "JWT_SECRET"
    "ENCRYPTION_KEY"
)

# Optional but recommended
recommended_vars=(
    "OPENAI_API_KEY"
    "ANTHROPIC_API_KEY"
    "SENDGRID_API_KEY"
)

# Check required variables
echo "Checking required variables..."
for var in "${required_vars[@]}"; do
    if [[ -z "${!var}" ]]; then
        echo "❌ Missing required variable: $var"
        exit 1
    else
        echo "✅ $var is set"
    fi
done

# Check recommended variables
echo "Checking recommended variables..."
for var in "${recommended_vars[@]}"; do
    if [[ -z "${!var}" ]]; then
        echo "⚠️  Missing recommended variable: $var"
    else
        echo "✅ $var is set"
    fi
done

# Validate JWT secret length
if [ ${#JWT_SECRET} -lt 32 ]; then
    echo "❌ JWT_SECRET must be at least 32 characters long"
    exit 1
fi

# Validate encryption key length
if [ ${#ENCRYPTION_KEY} -lt 32 ]; then
    echo "❌ ENCRYPTION_KEY must be at least 32 characters long"  
    exit 1
fi

echo "✅ Configuration validation completed successfully!"
```

## Monitoring Setup

### Prometheus Configuration

#### Prometheus Configuration (prometheus.yml)
```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093

rule_files:
  - "/etc/prometheus/rules/*.yml"

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'content-manager'
    static_configs:
      - targets: ['content-manager:8000']
    metrics_path: '/metrics'
    scrape_interval: 30s

  - job_name: 'ai-processor'
    static_configs:
      - targets: ['ai-processor:8001']
    metrics_path: '/metrics'
    scrape_interval: 30s

  - job_name: 'postgres-exporter'
    static_configs:
      - targets: ['postgres-exporter:9187']

  - job_name: 'redis-exporter'
    static_configs:
      - targets: ['redis-exporter:9121']

  - job_name: 'node-exporter'
    static_configs:
      - targets: ['node-exporter:9100']
```

#### Alert Rules (alert-rules.yml)
```yaml
groups:
- name: aquascene-content-engine
  rules:
  - alert: HighErrorRate
    expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High error rate detected"
      description: "Error rate is {{ $value }} errors per second"

  - alert: HighResponseTime
    expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 10
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High response time detected"
      description: "95th percentile response time is {{ $value }} seconds"

  - alert: ServiceDown
    expr: up == 0
    for: 1m
    labels:
      severity: critical
    annotations:
      summary: "Service is down"
      description: "{{ $labels.job }} has been down for more than 1 minute"

  - alert: DatabaseConnectionFailed
    expr: postgres_up == 0
    for: 2m
    labels:
      severity: critical
    annotations:
      summary: "Database connection failed"
      description: "Cannot connect to PostgreSQL database"

  - alert: RedisConnectionFailed
    expr: redis_up == 0
    for: 2m
    labels:
      severity: critical
    annotations:
      summary: "Redis connection failed"
      description: "Cannot connect to Redis cache"

  - alert: HighMemoryUsage
    expr: (container_memory_usage_bytes / container_spec_memory_limit_bytes) * 100 > 80
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High memory usage"
      description: "Container {{ $labels.name }} is using {{ $value }}% of available memory"

  - alert: DiskSpaceLow
    expr: (node_filesystem_avail_bytes / node_filesystem_size_bytes) * 100 < 10
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: "Disk space low"
      description: "Disk space is below 10% on {{ $labels.instance }}"
```

### Grafana Dashboard Setup

#### Dashboard Provisioning
```yaml
# infrastructure/monitoring/grafana/provisioning/dashboards/dashboard.yml
apiVersion: 1

providers:
- name: 'default'
  orgId: 1
  folder: ''
  type: file
  disableDeletion: false
  updateIntervalSeconds: 10
  allowUiUpdates: true
  options:
    path: /var/lib/grafana/dashboards
```

#### Data Source Configuration
```yaml
# infrastructure/monitoring/grafana/provisioning/datasources/prometheus.yml
apiVersion: 1

datasources:
- name: Prometheus
  type: prometheus
  access: proxy
  url: http://prometheus:9090
  isDefault: true
  editable: true
```

### Log Aggregation

#### Loki Configuration
```yaml
# infrastructure/logging/loki.yml
auth_enabled: false

server:
  http_listen_port: 3100
  grpc_listen_port: 9096

common:
  path_prefix: /loki
  storage:
    filesystem:
      chunks_directory: /loki/chunks
      rules_directory: /loki/rules
  replication_factor: 1
  ring:
    instance_addr: 127.0.0.1
    kvstore:
      store: inmemory

schema_config:
  configs:
    - from: 2020-10-24
      store: boltdb-shipper
      object_store: filesystem
      schema: v11
      index:
        prefix: index_
        period: 24h

ruler:
  alertmanager_url: http://localhost:9093

analytics:
  reporting_enabled: false
```

#### Promtail Configuration
```yaml
# infrastructure/logging/promtail.yml
server:
  http_listen_port: 9080
  grpc_listen_port: 0

positions:
  filename: /tmp/positions.yaml

clients:
  - url: http://loki:3100/loki/api/v1/push

scrape_configs:
- job_name: containers
  static_configs:
  - targets:
      - localhost
    labels:
      job: containerlogs
      __path__: /var/log/containers/*log
      
- job_name: system
  static_configs:
  - targets:
      - localhost
    labels:
      job: syslog
      __path__: /var/log/syslog
```

## Backup and Recovery

### Database Backup Strategy

#### Automated Backup Script
```bash
#!/bin/bash
# scripts/backup-database.sh

set -e

# Configuration
BACKUP_DIR="/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="content_engine_backup_${TIMESTAMP}.sql"
RETENTION_DAYS=30

# Load environment variables
source .env

echo "Starting database backup at $(date)"

# Create backup directory if it doesn't exist
mkdir -p $BACKUP_DIR

# Perform database backup
docker exec content-engine-postgres-prod pg_dump \
    -U $DB_USER \
    -d $DB_NAME \
    --clean \
    --if-exists \
    --verbose \
    > "${BACKUP_DIR}/${BACKUP_FILE}"

# Compress backup
gzip "${BACKUP_DIR}/${BACKUP_FILE}"

# Remove old backups
find $BACKUP_DIR -name "content_engine_backup_*.sql.gz" -mtime +$RETENTION_DAYS -delete

echo "Database backup completed: ${BACKUP_FILE}.gz"

# Upload to cloud storage (if configured)
if [ ! -z "$BACKUP_S3_BUCKET" ]; then
    aws s3 cp "${BACKUP_DIR}/${BACKUP_FILE}.gz" \
        "s3://$BACKUP_S3_BUCKET/database-backups/" \
        --region $BACKUP_S3_REGION
    echo "Backup uploaded to S3"
fi
```

#### Database Recovery Script
```bash
#!/bin/bash
# scripts/restore-database.sh

set -e

if [ $# -eq 0 ]; then
    echo "Usage: $0 <backup-file>"
    exit 1
fi

BACKUP_FILE=$1

if [ ! -f "$BACKUP_FILE" ]; then
    echo "Backup file not found: $BACKUP_FILE"
    exit 1
fi

# Load environment variables
source .env

echo "WARNING: This will replace the current database!"
read -p "Are you sure you want to continue? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Restore cancelled"
    exit 1
fi

echo "Starting database restore from $BACKUP_FILE"

# Stop application services
echo "Stopping application services..."
docker-compose stop content-manager ai-processor web-scraper subscriber-manager distributor

# Restore database
if [[ $BACKUP_FILE == *.gz ]]; then
    gunzip -c $BACKUP_FILE | docker exec -i content-engine-postgres-prod psql -U $DB_USER -d $DB_NAME
else
    cat $BACKUP_FILE | docker exec -i content-engine-postgres-prod psql -U $DB_USER -d $DB_NAME
fi

echo "Database restore completed"

# Start application services
echo "Starting application services..."
docker-compose start content-manager ai-processor web-scraper subscriber-manager distributor

echo "Database restore completed successfully"
```

### Full System Backup

#### Complete Backup Script
```bash
#!/bin/bash
# scripts/full-backup.sh

set -e

BACKUP_ROOT="/backups/full"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="${BACKUP_ROOT}/${TIMESTAMP}"

echo "Starting full system backup at $(date)"

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup database
echo "Backing up database..."
./scripts/backup-database.sh
cp /backups/content_engine_backup_*.sql.gz $BACKUP_DIR/

# Backup Docker volumes
echo "Backing up Docker volumes..."
docker run --rm \
    -v content_engine_postgres_data:/source:ro \
    -v $BACKUP_DIR:/backup \
    alpine \
    tar czf /backup/postgres_data.tar.gz -C /source .

docker run --rm \
    -v content_engine_redis_data:/source:ro \
    -v $BACKUP_DIR:/backup \
    alpine \
    tar czf /backup/redis_data.tar.gz -C /source .

docker run --rm \
    -v content_engine_minio_data:/source:ro \
    -v $BACKUP_DIR:/backup \
    alpine \
    tar czf /backup/minio_data.tar.gz -C /source .

# Backup configuration files
echo "Backing up configuration..."
tar czf $BACKUP_DIR/config.tar.gz .env docker-compose*.yml infrastructure/

# Backup application logs
echo "Backing up logs..."
tar czf $BACKUP_DIR/logs.tar.gz logs/

# Create backup manifest
echo "Creating backup manifest..."
cat > $BACKUP_DIR/manifest.txt << EOF
AquaScene Content Engine Full Backup
Timestamp: $(date)
Version: $(git describe --tags --always 2>/dev/null || echo "unknown")
Commit: $(git rev-parse HEAD 2>/dev/null || echo "unknown")

Files included:
- database backup (PostgreSQL)
- Docker volumes (postgres, redis, minio)
- Configuration files (.env, docker-compose.yml, infrastructure/)
- Application logs

To restore:
1. Stop all services: docker-compose down
2. Restore volumes: ./scripts/restore-volumes.sh $BACKUP_DIR
3. Restore database: ./scripts/restore-database.sh $BACKUP_DIR/content_engine_backup_*.sql.gz
4. Start services: docker-compose up -d
EOF

echo "Full system backup completed: $BACKUP_DIR"

# Clean up old backups (keep last 7 days)
find $BACKUP_ROOT -maxdepth 1 -type d -mtime +7 -exec rm -rf {} \;
```

## Security Configuration

### SSL/TLS Setup

#### Nginx SSL Configuration
```nginx
# infrastructure/nginx/ssl.conf
server {
    listen 80;
    server_name your-domain.com api.your-domain.com admin.your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    ssl_certificate /etc/ssl/certs/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/ssl/certs/your-domain.com/privkey.pem;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-Frame-Options DENY always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    
    location / {
        proxy_pass http://content-manager:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

server {
    listen 443 ssl http2;
    server_name api.your-domain.com;
    
    ssl_certificate /etc/ssl/certs/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/ssl/certs/your-domain.com/privkey.pem;
    
    # Same SSL configuration as above
    
    location /ai/ {
        proxy_pass http://ai-processor:8001/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location / {
        proxy_pass http://content-manager:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Firewall Configuration

#### UFW Firewall Setup
```bash
# Basic firewall setup
sudo ufw --force reset
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Allow SSH
sudo ufw allow 22/tcp

# Allow HTTP and HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Allow monitoring (restrict to specific IPs in production)
sudo ufw allow from 10.0.0.0/8 to any port 9090  # Prometheus
sudo ufw allow from 10.0.0.0/8 to any port 3000  # Grafana

# Enable firewall
sudo ufw --force enable

# Check status
sudo ufw status verbose
```

### Secret Management

#### Docker Secrets (Docker Swarm)
```bash
# Create secrets
echo "your_db_password" | docker secret create db_password -
echo "your_jwt_secret" | docker secret create jwt_secret -
echo "sk-your-openai-key" | docker secret create openai_api_key -

# Use in docker-compose.yml
version: '3.8'
services:
  content-manager:
    secrets:
      - db_password
      - jwt_secret
    environment:
      - DB_PASSWORD_FILE=/run/secrets/db_password
      - JWT_SECRET_FILE=/run/secrets/jwt_secret

secrets:
  db_password:
    external: true
  jwt_secret:
    external: true
  openai_api_key:
    external: true
```

#### HashiCorp Vault Integration (Advanced)
```python
# vault_config.py
import hvac
import os

class VaultConfig:
    def __init__(self):
        self.client = hvac.Client(
            url=os.getenv('VAULT_URL', 'https://vault.example.com'),
            token=os.getenv('VAULT_TOKEN')
        )
    
    def get_secret(self, path: str) -> dict:
        """Retrieve secret from Vault"""
        response = self.client.secrets.kv.v2.read_secret_version(path=path)
        return response['data']['data']
    
    def get_database_config(self) -> dict:
        """Get database configuration from Vault"""
        return self.get_secret('database/config')
    
    def get_api_keys(self) -> dict:
        """Get API keys from Vault"""
        return self.get_secret('api-keys/llm-providers')
```

## Troubleshooting

### Common Deployment Issues

#### Container Startup Issues
```bash
# Check container status
docker ps -a

# Check container logs
docker logs content-manager
docker logs ai-processor

# Check resource usage
docker stats

# Restart specific service
docker-compose restart content-manager

# Rebuild and restart
docker-compose build content-manager
docker-compose up -d content-manager
```

#### Network Issues
```bash
# Check Docker networks
docker network ls
docker network inspect content-engine_content-engine

# Test service connectivity
docker exec -it content-manager curl http://ai-processor:8001/health
docker exec -it ai-processor curl http://postgres:5432

# DNS resolution test
docker exec -it content-manager nslookup postgres
docker exec -it content-manager nslookup redis
```

#### Database Issues
```bash
# Check PostgreSQL status
docker exec -it postgres pg_isready -U postgres

# Connect to database
docker exec -it postgres psql -U postgres -d content_engine

# Check database size
docker exec -it postgres psql -U postgres -c "
    SELECT pg_database.datname,
           pg_size_pretty(pg_database_size(pg_database.datname)) AS size
    FROM pg_database;"

# Check connections
docker exec -it postgres psql -U postgres -c "
    SELECT count(*) as active_connections 
    FROM pg_stat_activity;"
```

#### Redis Issues
```bash
# Check Redis status
docker exec -it redis redis-cli ping

# Check Redis info
docker exec -it redis redis-cli info

# Monitor Redis commands
docker exec -it redis redis-cli monitor

# Check memory usage
docker exec -it redis redis-cli info memory
```

### Performance Issues

#### Memory Issues
```bash
# Check memory usage
free -h
docker stats --no-stream

# Check for memory leaks
docker exec -it content-manager ps aux
docker exec -it ai-processor ps aux

# Restart services if needed
docker-compose restart content-manager ai-processor
```

#### CPU Issues
```bash
# Check CPU usage
htop
docker stats --no-stream

# Check service load
docker exec -it content-manager curl http://localhost:8000/stats
docker exec -it ai-processor curl http://localhost:8001/stats

# Scale services if needed (Docker Swarm)
docker service scale aquascene_content-manager=3
docker service scale aquascene_ai-processor=2
```

#### Disk Space Issues
```bash
# Check disk usage
df -h

# Check Docker disk usage
docker system df

# Clean up Docker resources
docker system prune -a
docker volume prune

# Clean up old logs
find logs/ -name "*.log" -mtime +7 -delete
```

### Log Analysis

#### Centralized Logging Commands
```bash
# View all service logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f ai-processor

# Search logs for errors
docker-compose logs | grep -i error

# View logs from specific time
docker-compose logs --since="2025-08-06T10:00:00"

# Export logs for analysis
docker-compose logs --no-color > system-logs.txt
```

#### Log Analysis with jq
```bash
# Parse JSON logs
docker-compose logs ai-processor --no-color | jq '.'

# Filter error logs
docker-compose logs ai-processor --no-color | jq 'select(.level == "ERROR")'

# Count log levels
docker-compose logs ai-processor --no-color | jq -r '.level' | sort | uniq -c
```

## Maintenance

### Regular Maintenance Tasks

#### Daily Tasks
```bash
#!/bin/bash
# scripts/daily-maintenance.sh

# Check service health
echo "Checking service health..."
curl -f http://localhost:8000/health || echo "Content Manager unhealthy"
curl -f http://localhost:8001/health || echo "AI Processor unhealthy"

# Check disk space
echo "Checking disk space..."
df -h | awk '$5 > 80 {print "WARNING: " $0}'

# Backup database
echo "Running database backup..."
./scripts/backup-database.sh

# Clean up old logs
echo "Cleaning up old logs..."
find logs/ -name "*.log" -mtime +7 -delete

# Update system packages (if needed)
if command -v apt-get >/dev/null; then
    sudo apt-get update && sudo apt-get upgrade -y
fi
```

#### Weekly Tasks  
```bash
#!/bin/bash
# scripts/weekly-maintenance.sh

# Full system backup
echo "Running full system backup..."
./scripts/full-backup.sh

# Docker cleanup
echo "Cleaning up Docker resources..."
docker system prune -f
docker image prune -f

# Update Docker images
echo "Updating Docker images..."
docker-compose pull
docker-compose up -d

# Performance check
echo "Running performance check..."
./scripts/performance-check.sh

# Security updates
echo "Checking for security updates..."
sudo apt list --upgradable | grep -i security
```

#### Monthly Tasks
```bash
#!/bin/bash
# scripts/monthly-maintenance.sh

# Certificate renewal (if using Let's Encrypt)
echo "Renewing SSL certificates..."
sudo certbot renew

# Database optimization
echo "Optimizing database..."
docker exec postgres psql -U postgres -d content_engine -c "VACUUM ANALYZE;"

# Review and rotate logs
echo "Rotating logs..."
logrotate /etc/logrotate.conf

# Security audit
echo "Running security audit..."
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
    -v /usr/local/bin/docker:/usr/local/bin/docker \
    aquasec/trivy image aquascene/ai-processor:latest

# Backup to external storage
echo "Backing up to external storage..."
if [ ! -z "$BACKUP_S3_BUCKET" ]; then
    aws s3 sync /backups/ s3://$BACKUP_S3_BUCKET/backups/ --delete
fi
```

### Update and Upgrade Procedures

#### Application Updates
```bash
#!/bin/bash
# scripts/update-application.sh

set -e

NEW_VERSION=$1

if [ -z "$NEW_VERSION" ]; then
    echo "Usage: $0 <new-version>"
    exit 1
fi

echo "Updating AquaScene Content Engine to version $NEW_VERSION"

# Pre-update backup
echo "Creating pre-update backup..."
./scripts/full-backup.sh

# Pull new images
echo "Pulling new images..."
export VERSION=$NEW_VERSION
docker-compose pull

# Rolling update (zero downtime)
echo "Performing rolling update..."
docker-compose up -d --no-deps content-manager
sleep 30
docker-compose up -d --no-deps ai-processor
sleep 30
docker-compose up -d --no-deps web-scraper
sleep 30
docker-compose up -d --no-deps subscriber-manager
sleep 30
docker-compose up -d --no-deps distributor

# Verify update
echo "Verifying update..."
sleep 60
./run-full-test-suite.sh

echo "Application update completed successfully!"
```

#### Database Migrations
```bash
#!/bin/bash
# scripts/run-migrations.sh

set -e

echo "Running database migrations..."

# Backup before migration
./scripts/backup-database.sh

# Run migrations
docker exec content-manager python -m alembic upgrade head

# Verify migration
docker exec postgres psql -U postgres -d content_engine -c "
    SELECT version_num FROM alembic_version;"

echo "Database migrations completed successfully!"
```

### Monitoring and Alerting

#### Health Check Script
```bash
#!/bin/bash
# scripts/health-check.sh

set -e

FAILED_CHECKS=0

# Function to check service health
check_service() {
    local service_name=$1
    local health_url=$2
    
    if curl -f -s $health_url > /dev/null; then
        echo "✅ $service_name is healthy"
    else
        echo "❌ $service_name is unhealthy"
        ((FAILED_CHECKS++))
    fi
}

echo "🏥 AquaScene Content Engine Health Check"
echo "========================================"

# Check core services
check_service "Content Manager" "http://localhost:8000/health"
check_service "AI Processor" "http://localhost:8001/health"
check_service "Web Scraper" "http://localhost:8002/health"
check_service "Subscriber Manager" "http://localhost:8004/health"

# Check infrastructure
check_service "Prometheus" "http://localhost:9090/-/healthy"
check_service "Grafana" "http://localhost:3000/api/health"

# Check database connectivity
if docker exec postgres pg_isready -U postgres -d content_engine > /dev/null 2>&1; then
    echo "✅ PostgreSQL is healthy"
else
    echo "❌ PostgreSQL is unhealthy"
    ((FAILED_CHECKS++))
fi

# Check Redis connectivity  
if docker exec redis redis-cli ping > /dev/null 2>&1; then
    echo "✅ Redis is healthy"
else
    echo "❌ Redis is unhealthy"
    ((FAILED_CHECKS++))
fi

echo "========================================"
if [ $FAILED_CHECKS -eq 0 ]; then
    echo "🎉 All services are healthy!"
    exit 0
else
    echo "⚠️  $FAILED_CHECKS service(s) are unhealthy"
    exit 1
fi
```

## Conclusion

This deployment guide provides comprehensive instructions for deploying the AquaScene Content Engine across all environments. Key points to remember:

1. **Always validate configuration** before deployment
2. **Use environment-specific configurations** for different stages
3. **Implement proper backup strategies** before any major changes
4. **Monitor system health** continuously
5. **Follow security best practices** for production deployments
6. **Maintain regular update cycles** for security and performance

### Quick Reference Commands

```bash
# Quick deployment
./fix-dependencies.sh && ./start-services.sh

# Health check
curl http://localhost:8000/health

# View all logs
docker-compose logs -f

# Restart all services
docker-compose restart

# Clean deployment
docker-compose down && docker-compose up -d

# Full test
./run-full-test-suite.sh

# Production deployment
docker-compose -f docker-compose.production.yml up -d
```

For additional support and troubleshooting, refer to the individual service documentation and the main troubleshooting guide.

---

**Document Status:** Complete ✅  
**Last Updated:** August 6, 2025  
**Next Review:** September 6, 2025  
**Owner:** AquaScene Operations Team