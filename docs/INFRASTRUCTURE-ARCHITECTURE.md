# AquaScene Content Engine - Infrastructure Architecture

## Table of Contents
1. [Infrastructure Overview](#infrastructure-overview)
2. [Container Architecture](#container-architecture)
3. [Networking Architecture](#networking-architecture)
4. [Storage Systems](#storage-systems)
5. [Monitoring and Observability](#monitoring-and-observability)
6. [Load Balancing and Reverse Proxy](#load-balancing-and-reverse-proxy)
7. [Service Discovery and Health Checks](#service-discovery-and-health-checks)
8. [Backup and Disaster Recovery](#backup-and-disaster-recovery)
9. [Environment Configurations](#environment-configurations)
10. [Infrastructure as Code](#infrastructure-as-code)

## Infrastructure Overview

The AquaScene Content Engine infrastructure is built on container-first principles using Docker and Docker Compose, designed for local development with production-ready patterns that can be deployed to Kubernetes or Docker Swarm.

### Infrastructure Stack
```yaml
Containerization: Docker 24.x + Docker Compose 2.x
Reverse Proxy: Nginx Alpine
Database: PostgreSQL 15 with connection pooling
Cache: Redis 7 with persistence
Object Storage: MinIO (S3-compatible)
Monitoring: Prometheus + Grafana + Loki stack
Log Aggregation: Promtail + Loki
Metrics: Prometheus exporters
Dashboards: Grafana with custom dashboards
Backup: Automated PostgreSQL + Redis backups
```

### Infrastructure Topology
```mermaid
graph TB
    subgraph "External Access"
        EXT[Internet/Users]
    end
    
    subgraph "Load Balancer Layer"
        LB[Nginx Reverse Proxy<br/>Port: 80, 443]
    end
    
    subgraph "Application Layer"
        CM[Content Manager<br/>Port: 8000]
        AI[AI Processor<br/>Port: 8001]
        WS[Web Scraper<br/>Port: 8002]
        DIST[Distributor<br/>Port: 8003]
        SUB[Subscriber Manager<br/>Port: 8004]
        ADMIN[Admin Dashboard<br/>Port: 3000]
    end
    
    subgraph "Data Layer"
        PG[(PostgreSQL<br/>Port: 5432)]
        REDIS[(Redis<br/>Port: 6379)]
        MINIO[(MinIO<br/>Port: 9000, 9001)]
    end
    
    subgraph "Monitoring Layer"
        PROM[Prometheus<br/>Port: 9090]
        GRAF[Grafana<br/>Port: 3000]
        LOKI[Loki<br/>Port: 3100]
        PROM_TAIL[Promtail]
        NODE_EXP[Node Exporter<br/>Port: 9100]
        CADV[cAdvisor<br/>Port: 8080]
    end
    
    subgraph "Infrastructure Services"
        BACKUP[Backup Service]
        HAPROXY[HAProxy<br/>Optional]
    end
    
    EXT --> LB
    LB --> ADMIN
    LB --> CM
    LB --> AI
    LB --> WS
    LB --> DIST
    LB --> SUB
    LB --> GRAF
    LB --> PROM
    
    CM --> PG
    CM --> REDIS
    AI --> PG
    AI --> REDIS
    WS --> PG
    WS --> REDIS
    DIST --> PG
    DIST --> REDIS
    DIST --> MINIO
    SUB --> PG
    SUB --> REDIS
    
    PROM --> CM
    PROM --> AI
    PROM --> WS
    PROM --> DIST
    PROM --> SUB
    PROM --> NODE_EXP
    PROM --> CADV
    PROM_TAIL --> LOKI
    LOKI --> GRAF
    PROM --> GRAF
    
    BACKUP --> PG
    BACKUP --> REDIS
    BACKUP --> MINIO
```

## Container Architecture

### Container Strategy and Design

#### Multi-Stage Build Pattern
```dockerfile
# Example: AI Processor Service Dockerfile
FROM python:3.11-slim as builder
WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

FROM python:3.11-slim as runtime
WORKDIR /app

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Install runtime dependencies only
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy Python packages from builder stage
COPY --from=builder /root/.local /home/appuser/.local

# Copy application code
COPY --chown=appuser:appuser src/ ./src/
COPY --chown=appuser:appuser config/ ./config/

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

# Expose port
EXPOSE 8001

# Run application
CMD ["python", "-m", "src.main"]
```

#### Container Resource Management
```yaml
# Docker Compose resource limits
services:
  content-manager:
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '1.0'
        reservations:
          memory: 512M
          cpus: '0.5'
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

### Container Networking

#### Network Segmentation
```yaml
# Docker Compose networks
networks:
  content-engine:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
          gateway: 172.20.0.1
  
  monitoring:
    driver: bridge
    ipam:
      config:
        - subnet: 172.21.0.0/16
          gateway: 172.21.0.1
  
  external:
    external: true
    name: shared-network
```

#### Service Communication Matrix
```yaml
Content Manager:
  Outbound: [ai-processor, web-scraper, distributor, subscriber-manager, postgres, redis]
  Inbound: [nginx, admin-dashboard]
  Network: content-engine

AI Processor:
  Outbound: [postgres, redis, external-apis]
  Inbound: [content-manager]
  Network: content-engine

Web Scraper:
  Outbound: [postgres, redis, external-web]
  Inbound: [content-manager]
  Network: content-engine

Distributor:
  Outbound: [postgres, redis, minio, sendgrid, instagram-api]
  Inbound: [content-manager]
  Network: content-engine

Subscriber Manager:
  Outbound: [postgres, redis]
  Inbound: [content-manager, distributor]
  Network: content-engine

Monitoring Stack:
  Network: monitoring
  Cross-Network: content-engine (for scraping metrics)
```

## Storage Systems

### PostgreSQL Configuration

#### Database Container Setup
```yaml
postgres:
  image: postgres:15
  container_name: content-engine-postgres
  restart: unless-stopped
  environment:
    POSTGRES_DB: ${DB_NAME:-content_engine}
    POSTGRES_USER: ${DB_USER:-postgres}
    POSTGRES_PASSWORD: ${DB_PASSWORD}
    POSTGRES_MULTIPLE_DATABASES: content_engine,content_engine_test
    PGDATA: /var/lib/postgresql/data/pgdata
  volumes:
    - postgres_data:/var/lib/postgresql/data
    - ./infrastructure/database/init:/docker-entrypoint-initdb.d:ro
    - ./infrastructure/database/backups:/backups
  ports:
    - "${DB_PORT:-5432}:5432"
  command: >
    postgres
    -c max_connections=200
    -c shared_buffers=256MB
    -c effective_cache_size=1GB
    -c maintenance_work_mem=64MB
    -c checkpoint_completion_target=0.9
    -c wal_buffers=16MB
    -c default_statistics_target=100
    -c random_page_cost=1.1
    -c effective_io_concurrency=200
    -c work_mem=4MB
    -c min_wal_size=1GB
    -c max_wal_size=4GB
    -c logging_collector=on
    -c log_directory='/var/log/postgresql'
    -c log_filename='postgresql-%Y-%m-%d_%H%M%S.log'
    -c log_statement='mod'
    -c log_min_duration_statement=1000
```

#### Connection Pooling Strategy
```yaml
# PgBouncer configuration (production)
pgbouncer:
  image: pgbouncer/pgbouncer:latest
  environment:
    DATABASES_HOST: postgres
    DATABASES_PORT: 5432
    DATABASES_USER: postgres
    DATABASES_PASSWORD: ${DB_PASSWORD}
    POOL_MODE: transaction
    SERVER_RESET_QUERY: DISCARD ALL
    MAX_CLIENT_CONN: 1000
    DEFAULT_POOL_SIZE: 25
    MAX_DB_CONNECTIONS: 100
  depends_on:
    - postgres
```

### Redis Configuration

#### Redis Cluster Setup
```yaml
redis:
  image: redis:7-alpine
  container_name: content-engine-redis
  restart: unless-stopped
  command: >
    redis-server
    --appendonly yes
    --appendfsync everysec
    --auto-aof-rewrite-percentage 100
    --auto-aof-rewrite-min-size 64mb
    --requirepass ${REDIS_PASSWORD}
    --maxmemory 512mb
    --maxmemory-policy allkeys-lru
    --tcp-keepalive 300
    --timeout 300
    --databases 16
    --save 900 1
    --save 300 10
    --save 60 10000
  volumes:
    - redis_data:/data
    - ./infrastructure/redis/redis.conf:/etc/redis/redis.conf:ro
  healthcheck:
    test: ["CMD", "redis-cli", "-a", "${REDIS_PASSWORD}", "ping"]
    interval: 10s
    timeout: 3s
    retries: 5
```

#### Redis Usage Patterns
```yaml
Database Allocation:
  DB 0: Content Manager (session cache, API cache)
  DB 1: AI Processor (job queues, model cache)
  DB 2: Web Scraper (request cache, rate limiting)
  DB 3: Distributor (email queues, social scheduling)
  DB 4: Subscriber Manager (user sessions, preferences cache)
  DB 5: System (health checks, monitoring)

Key Patterns:
  Sessions: "session:{uuid}"
  Cache: "cache:{service}:{key}"
  Queues: "queue:{service}:{type}"
  Locks: "lock:{resource}:{id}"
  Counters: "counter:{metric}:{period}"
  Sets: "set:{category}:{identifier}"
```

### MinIO Object Storage

#### MinIO Configuration
```yaml
minio:
  image: minio/minio:latest
  container_name: content-engine-minio
  restart: unless-stopped
  command: server /data --console-address ":9001"
  environment:
    MINIO_ROOT_USER: ${MINIO_ROOT_USER:-admin}
    MINIO_ROOT_PASSWORD: ${MINIO_ROOT_PASSWORD}
    MINIO_BROWSER_REDIRECT_URL: http://localhost:9001
  volumes:
    - minio_data:/data
  ports:
    - "9000:9000"   # API
    - "9001:9001"   # Console
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
    interval: 30s
    timeout: 20s
    retries: 3
```

#### Storage Bucket Strategy
```yaml
Buckets:
  content-assets:
    Purpose: Generated content images, documents
    Access: Private with signed URLs
    Retention: Permanent
    Versioning: Enabled
    
  newsletter-templates:
    Purpose: Email template assets
    Access: Private
    Retention: Permanent
    Versioning: Enabled
    
  instagram-media:
    Purpose: Instagram post images/videos
    Access: Private with signed URLs
    Retention: 1 year
    Versioning: Disabled
    
  system-backups:
    Purpose: Database and configuration backups
    Access: Private
    Retention: 30 days
    Versioning: Enabled
    
  temp-uploads:
    Purpose: Temporary file uploads
    Access: Private
    Retention: 24 hours (lifecycle policy)
    Versioning: Disabled
```

## Load Balancing and Reverse Proxy

### Nginx Configuration Architecture

#### Main Configuration Structure
```nginx
# /etc/nginx/nginx.conf
worker_processes auto;
worker_rlimit_nofile 65535;

events {
    worker_connections 4096;
    use epoll;
    multi_accept on;
    worker_aio_requests 32;
}

http {
    # Performance optimizations
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    keepalive_requests 100;
    
    # Compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_comp_level 6;
    gzip_types
        text/plain
        text/css
        application/json
        application/javascript
        text/xml
        application/xml
        application/xml+rss
        text/javascript;
    
    # Rate limiting zones
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=admin:10m rate=5r/s;
    limit_req_zone $binary_remote_addr zone=ai:10m rate=2r/s;
    
    # Upstream definitions
    include /etc/nginx/upstream.conf;
    
    # Server configurations
    include /etc/nginx/sites-enabled/*;
}
```

#### Upstream Configuration
```nginx
# /etc/nginx/upstream.conf
upstream content_manager {
    least_conn;
    server content-manager:8000 max_fails=3 fail_timeout=30s weight=1;
    keepalive 32;
    keepalive_requests 100;
    keepalive_timeout 60s;
}

upstream ai_processor {
    ip_hash; # Sticky sessions for long-running AI tasks
    server ai-processor:8001 max_fails=2 fail_timeout=60s;
    keepalive 16;
}

upstream web_scraper {
    least_conn;
    server web-scraper:8002 max_fails=3 fail_timeout=30s;
    keepalive 8;
}

upstream distributor {
    least_conn;
    server distributor:8003 max_fails=3 fail_timeout=30s;
    keepalive 16;
}

upstream subscriber_manager {
    least_conn;
    server subscriber-manager:8004 max_fails=3 fail_timeout=30s;
    keepalive 16;
}

upstream admin_dashboard {
    server admin-dashboard:3000 max_fails=2 fail_timeout=30s;
    keepalive 8;
}
```

#### SSL/TLS Configuration (Production)
```nginx
# SSL configuration
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-AES128-SHA256:ECDHE-RSA-AES256-SHA384:ECDHE-RSA-AES128-SHA:ECDHE-RSA-AES256-SHA:DHE-RSA-AES128-SHA256:DHE-RSA-AES256-SHA256:DHE-RSA-AES128-SHA:DHE-RSA-AES256-SHA;
ssl_prefer_server_ciphers off;
ssl_session_cache shared:SSL:10m;
ssl_session_timeout 10m;
ssl_stapling on;
ssl_stapling_verify on;

# HSTS
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
```

### Load Balancing Strategies

#### Service-Specific Load Balancing
```yaml
Content Manager:
  Strategy: least_conn
  Reason: Balanced load distribution for API requests
  Health Check: /health endpoint
  Failover: 3 failures in 30 seconds
  
AI Processor:
  Strategy: ip_hash
  Reason: Maintain session affinity for long-running tasks
  Health Check: /health endpoint  
  Timeout: Extended (300s) for AI processing
  
Web Scraper:
  Strategy: least_conn
  Reason: Distributed scraping load
  Health Check: /health endpoint
  Rate Limiting: Aggressive to prevent abuse
  
Distributor:
  Strategy: round_robin
  Reason: Even distribution of email/social tasks
  Health Check: /health endpoint
  Circuit Breaker: Fail fast for external service issues
```

## Monitoring and Observability

### Prometheus Configuration

#### Prometheus Setup
```yaml
prometheus:
  image: prom/prometheus:latest
  container_name: content-engine-prometheus
  restart: unless-stopped
  command:
    - '--config.file=/etc/prometheus/prometheus.yml'
    - '--storage.tsdb.path=/prometheus'
    - '--web.console.libraries=/etc/prometheus/console_libraries'
    - '--web.console.templates=/etc/prometheus/consoles'
    - '--storage.tsdb.retention.time=30d'
    - '--storage.tsdb.retention.size=10GB'
    - '--web.enable-lifecycle'
    - '--web.enable-admin-api'
    - '--web.enable-remote-write-receiver'
  volumes:
    - ./infrastructure/monitoring/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml:ro
    - ./infrastructure/monitoring/prometheus/rules:/etc/prometheus/rules:ro
    - prometheus_data:/prometheus
  ports:
    - "9090:9090"
```

#### Scrape Configuration
```yaml
# prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    cluster: 'content-engine'
    environment: 'development'

rule_files:
  - "rules/*.yml"

scrape_configs:
  # Self-monitoring
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']
    scrape_interval: 10s

  # System monitoring
  - job_name: 'node-exporter'
    static_configs:
      - targets: ['node-exporter:9100']
    scrape_interval: 15s

  - job_name: 'cadvisor'
    static_configs:
      - targets: ['cadvisor:8080']
    scrape_interval: 15s

  # Application services
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
    scrape_timeout: 20s

  # Database monitoring
  - job_name: 'postgres-exporter'
    static_configs:
      - targets: ['postgres-exporter:9187']
    scrape_interval: 30s

  - job_name: 'redis-exporter'
    static_configs:
      - targets: ['redis-exporter:9121']
    scrape_interval: 30s
```

### Grafana Configuration

#### Grafana Setup with Provisioning
```yaml
grafana:
  image: grafana/grafana:latest
  container_name: content-engine-grafana
  restart: unless-stopped
  environment:
    - GF_SECURITY_ADMIN_USER=${GRAFANA_USER:-admin}
    - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD}
    - GF_INSTALL_PLUGINS=redis-datasource,postgres-datasource
    - GF_FEATURE_TOGGLES_ENABLE=publicDashboards
    - GF_SMTP_ENABLED=true
    - GF_SMTP_HOST=${SMTP_HOST}
    - GF_SMTP_FROM_ADDRESS=monitoring@aquascene.com
  volumes:
    - grafana_data:/var/lib/grafana
    - ./infrastructure/monitoring/grafana/provisioning:/etc/grafana/provisioning:ro
    - ./infrastructure/monitoring/grafana/dashboards:/var/lib/grafana/dashboards:ro
  ports:
    - "3000:3000"
```

#### Dashboard Provisioning
```yaml
# provisioning/dashboards/dashboard.yml
apiVersion: 1

providers:
  - name: 'default'
    orgId: 1
    folder: 'AquaScene Content Engine'
    type: file
    disableDeletion: false
    updateIntervalSeconds: 10
    allowUiUpdates: true
    options:
      path: /var/lib/grafana/dashboards

# provisioning/datasources/datasource.yml
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    
  - name: Loki
    type: loki
    access: proxy
    url: http://loki:3100
    
  - name: PostgreSQL
    type: postgres
    url: postgres:5432
    database: content_engine
    user: ${DB_USER}
    secureJsonData:
      password: ${DB_PASSWORD}
```

### Logging Architecture

#### Loki Configuration
```yaml
loki:
  image: grafana/loki:latest
  container_name: content-engine-loki
  restart: unless-stopped
  command: -config.file=/etc/loki/local-config.yaml
  volumes:
    - ./infrastructure/logging/loki.yml:/etc/loki/local-config.yaml:ro
    - loki_data:/loki
  ports:
    - "3100:3100"

promtail:
  image: grafana/promtail:latest
  container_name: content-engine-promtail
  restart: unless-stopped
  command: -config.file=/etc/promtail/config.yml
  volumes:
    - ./infrastructure/logging/promtail.yml:/etc/promtail/config.yml:ro
    - /var/log:/var/log:ro
    - /var/lib/docker/containers:/var/lib/docker/containers:ro
    - /var/run/docker.sock:/var/run/docker.sock:ro
```

#### Log Aggregation Configuration
```yaml
# loki.yml
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

# promtail.yml
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
          __path__: /var/lib/docker/containers/*/*log

    pipeline_stages:
      - json:
          expressions:
            output: log
            stream: stream
            attrs:
      - json:
          expressions:
            tag:
          source: attrs
      - regex:
          expression: (?P<container_name>(?:[^|]*))\|
          source: tag
      - timestamp:
          format: RFC3339Nano
          source: time
      - labels:
          stream:
          container_name:
      - output:
          source: output
```

## Service Discovery and Health Checks

### Health Check Strategy
```yaml
# Health check endpoints across services
Health Check Pattern:
  Path: /health
  Method: GET
  Response: JSON with status and metadata
  Timeout: 10 seconds
  Interval: 30 seconds
  Retries: 3
  Start Period: 40 seconds (AI service may need longer)

Response Format:
  {
    "status": "healthy|unhealthy|degraded",
    "timestamp": "2024-01-15T10:30:00Z",
    "version": "1.0.0",
    "checks": {
      "database": "healthy",
      "redis": "healthy", 
      "external_services": "healthy"
    },
    "metadata": {
      "uptime": 3600,
      "memory_usage": "45%",
      "active_connections": 12
    }
  }
```

### Service Discovery
```yaml
Development Environment:
  Method: Docker Compose service names
  Discovery: Built-in Docker DNS
  Load Balancing: Nginx upstream blocks
  
Production Environment:
  Method: Kubernetes service discovery / Consul
  Discovery: DNS-based service discovery
  Load Balancing: Kubernetes services / HAProxy
  Health Checks: Kubernetes liveness/readiness probes
```

## Backup and Disaster Recovery

### Backup Service Configuration
```yaml
backup-service:
  build:
    context: ./infrastructure/backup
    dockerfile: Dockerfile
  container_name: content-engine-backup
  restart: unless-stopped
  environment:
    - DATABASE_URL=postgresql://${DB_USER}:${DB_PASSWORD}@postgres:5432/${DB_NAME}
    - REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379
    - MINIO_ENDPOINT=minio:9000
    - MINIO_ACCESS_KEY=${MINIO_ROOT_USER}
    - MINIO_SECRET_KEY=${MINIO_ROOT_PASSWORD}
    - BACKUP_SCHEDULE=${BACKUP_SCHEDULE:-0 2 * * *}
    - BACKUP_RETENTION_DAYS=${BACKUP_RETENTION_DAYS:-30}
    - S3_ENDPOINT=${S3_ENDPOINT}
    - S3_ACCESS_KEY=${S3_ACCESS_KEY}
    - S3_SECRET_KEY=${S3_SECRET_KEY}
    - S3_BUCKET=${S3_BACKUP_BUCKET:-content-engine-backups}
  volumes:
    - backup_data:/backups
    - ./infrastructure/database/backups:/database-backups
```

### Backup Strategy Implementation
```bash
#!/bin/bash
# backup-script.sh

# Database backup
pg_dump -h postgres -U $DB_USER -d $DB_NAME --clean --if-exists --create > \
  /backups/postgres_$(date +%Y%m%d_%H%M%S).sql

# Redis backup
redis-cli -h redis -a $REDIS_PASSWORD --rdb /backups/redis_$(date +%Y%m%d_%H%M%S).rdb

# MinIO backup (sync to external S3)
mc mirror minio/content-assets s3/backup-bucket/content-assets
mc mirror minio/newsletter-templates s3/backup-bucket/newsletter-templates

# Configuration backup
tar -czf /backups/config_$(date +%Y%m%d_%H%M%S).tar.gz \
  /app/config \
  /app/infrastructure \
  /app/docker-compose*.yml

# Cleanup old backups (keep last 30 days)
find /backups -name "*.sql" -mtime +30 -delete
find /backups -name "*.rdb" -mtime +30 -delete
find /backups -name "*.tar.gz" -mtime +30 -delete
```

### Disaster Recovery Plan
```yaml
Recovery Time Objectives:
  Database Recovery: 1 hour maximum
  Application Recovery: 30 minutes
  Full System Recovery: 2 hours maximum

Recovery Point Objectives:
  Database: 5 minutes maximum data loss
  File Storage: 15 minutes maximum
  Configuration: 1 hour maximum

Recovery Procedures:
  1. Database Restore:
     - Stop application services
     - Restore PostgreSQL from latest backup
     - Verify data integrity
     - Restart services
     
  2. Redis Recovery:
     - Redis has built-in persistence (AOF + RDB)
     - Automatic recovery on restart
     - Manual restore from backup if needed
     
  3. MinIO Recovery:
     - Distributed storage with erasure coding
     - Automatic data recovery
     - Restore from S3 backup if needed
     
  4. Configuration Recovery:
     - Restore from Git repository
     - Apply environment-specific configurations
     - Validate service connectivity
```

## Environment Configurations

### Multi-Environment Strategy
```yaml
Development (docker-compose.yml):
  Services: All services running locally
  Database: Single PostgreSQL instance
  Cache: Single Redis instance
  Monitoring: Local Prometheus/Grafana
  SSL: Disabled
  Debug: Enabled
  Hot Reload: Enabled
  External APIs: Sandbox/test endpoints

Staging (docker-compose.staging.yml):
  Services: Production-like setup
  Database: PostgreSQL with read replica
  Cache: Redis with persistence
  Monitoring: Full monitoring stack
  SSL: Let's Encrypt certificates
  Debug: Limited
  Hot Reload: Disabled
  External APIs: Production endpoints (limited usage)

Production (docker-compose.production.yml):
  Services: Highly available setup
  Database: PostgreSQL cluster with failover
  Cache: Redis cluster
  Monitoring: Enterprise monitoring with alerting
  SSL: Production certificates
  Debug: Disabled
  Hot Reload: Disabled  
  External APIs: Production endpoints
  Backup: Automated backup with retention
  Logging: Centralized logging
```

### Configuration Management
```yaml
Environment Variables:
  Database:
    - DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
    - DB_POOL_SIZE, DB_MAX_OVERFLOW
    
  Redis:
    - REDIS_HOST, REDIS_PORT, REDIS_PASSWORD
    - REDIS_POOL_SIZE, REDIS_TIMEOUT
    
  External APIs:
    - OPENAI_API_KEY, ANTHROPIC_API_KEY
    - SENDGRID_API_KEY, INSTAGRAM_ACCESS_TOKEN
    
  Security:
    - JWT_SECRET, ENCRYPTION_KEY
    - ALLOWED_ORIGINS, RATE_LIMIT_CONFIG
    
  Monitoring:
    - GRAFANA_USER, GRAFANA_PASSWORD
    - PROMETHEUS_RETENTION, LOG_LEVEL

Secrets Management:
  Development: .env files (not committed)
  Staging: Docker secrets / HashiCorp Vault
  Production: Kubernetes secrets / AWS Secrets Manager
```

## Infrastructure as Code

### Docker Compose as Infrastructure
```yaml
# Infrastructure components defined as code
version: '3.8'

x-logging: &default-logging
  logging:
    driver: "json-file"
    options:
      max-size: "10m"
      max-file: "3"

x-restart-policy: &default-restart-policy
  restart: unless-stopped

x-healthcheck-defaults: &default-healthcheck
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s

services:
  # Services inherit common configuration
  content-manager:
    <<: [*default-logging, *default-restart-policy]
    healthcheck:
      <<: *default-healthcheck
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
```

### Infrastructure Validation
```bash
#!/bin/bash
# validate-infrastructure.sh

echo "Validating infrastructure configuration..."

# Check Docker Compose syntax
docker-compose config --quiet
if [ $? -eq 0 ]; then
    echo "✓ Docker Compose configuration valid"
else
    echo "✗ Docker Compose configuration invalid"
    exit 1
fi

# Validate network configuration
echo "Validating network configuration..."
docker network inspect content-engine >/dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✓ Network configuration valid"
else
    echo "✗ Network configuration invalid"
fi

# Check volume mounts
echo "Validating volume mounts..."
for volume in postgres_data redis_data minio_data grafana_data prometheus_data; do
    docker volume inspect $volume >/dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo "✓ Volume $volume exists"
    else
        echo "? Volume $volume will be created"
    fi
done

# Validate service health
echo "Checking service health..."
for service in content-manager ai-processor web-scraper distributor subscriber-manager; do
    curl -f http://localhost:8000/health >/dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo "✓ Service $service healthy"
    else
        echo "! Service $service not responding (may not be started)"
    fi
done

echo "Infrastructure validation complete"
```

This comprehensive infrastructure architecture documentation provides the technical foundation for deploying, managing, and scaling the AquaScene Content Engine across different environments while maintaining high availability, performance, and observability.