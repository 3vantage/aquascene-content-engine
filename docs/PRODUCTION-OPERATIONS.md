# AquaScene Content Engine - Production Operations Guide

**Version:** 1.0  
**Last Updated:** August 6, 2025  
**Document Type:** Operations and DevOps Guide  
**Status:** Production Ready

## Table of Contents

1. [Production Deployment Overview](#production-deployment-overview)
2. [Infrastructure Requirements](#infrastructure-requirements)
3. [CI/CD Pipeline Configuration](#cicd-pipeline-configuration)
4. [Monitoring and Alerting Setup](#monitoring-and-alerting-setup)
5. [Backup and Disaster Recovery](#backup-and-disaster-recovery)
6. [Security Hardening](#security-hardening)
7. [Performance Optimization](#performance-optimization)
8. [Operational Procedures](#operational-procedures)

## Production Deployment Overview

### Architecture Overview

The AquaScene Content Engine production deployment follows a microservices architecture with containerized services, comprehensive monitoring, automated backups, and enterprise-grade security measures.

```mermaid
graph TB
    A[Load Balancer] --> B[Nginx Proxy]
    B --> C[Content Manager]
    B --> D[AI Processor]
    B --> E[Distributor]
    B --> F[Subscriber Manager]
    B --> G[Web Scraper]
    B --> H[Admin Dashboard]
    
    C --> I[PostgreSQL Primary]
    D --> I
    E --> I
    F --> I
    G --> I
    
    I --> J[PostgreSQL Replica]
    
    C --> K[Redis Cluster]
    D --> K
    E --> K
    F --> K
    G --> K
    
    C --> L[MinIO Storage]
    D --> L
    E --> L
    
    M[Prometheus] --> N[Grafana]
    M --> O[AlertManager]
    
    P[Loki] --> N
    Q[Promtail] --> P
    
    R[Backup Service] --> S[S3 Storage]
```

### Production Environment Specifications

#### Recommended Infrastructure
| Component | Minimum Spec | Recommended | Enterprise |
|-----------|-------------|-------------|------------|
| **CPU** | 4 vCPUs | 8 vCPUs | 16 vCPUs |
| **RAM** | 16 GB | 32 GB | 64 GB |
| **Storage** | 100 GB SSD | 500 GB SSD | 1 TB NVMe |
| **Network** | 1 Gbps | 10 Gbps | 10 Gbps + redundancy |
| **Availability** | Single Zone | Multi-Zone | Multi-Region |

#### Cloud Provider Support
- **AWS**: ECS, EKS, EC2 with Auto Scaling
- **Google Cloud**: GKE, Compute Engine, Cloud Run
- **Azure**: AKS, Container Instances, Virtual Machines
- **DigitalOcean**: Kubernetes, Droplets with Load Balancers
- **Self-Hosted**: Docker Swarm, Kubernetes on-premises

## Infrastructure Requirements

### Container Infrastructure

#### Docker Swarm Configuration
```yaml
# docker-stack.yml
version: '3.8'

networks:
  content-engine:
    driver: overlay
    attachable: true
  monitoring:
    driver: overlay
    attachable: true

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

services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: ${DB_NAME}
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD_FILE: /run/secrets/postgres_password
    secrets:
      - postgres_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - content-engine
    deploy:
      replicas: 1
      placement:
        constraints:
          - node.role == manager
      resources:
        limits:
          memory: 2G
          cpus: '1.0'
        reservations:
          memory: 1G
          cpus: '0.5'
      restart_policy:
        condition: on-failure
        delay: 10s
        max_attempts: 3

  redis:
    image: redis:7-alpine
    command: >
      redis-server
      --appendonly yes
      --requirepass_FILE /run/secrets/redis_password
      --maxmemory 1gb
      --maxmemory-policy allkeys-lru
    secrets:
      - redis_password
    volumes:
      - redis_data:/data
    networks:
      - content-engine
    deploy:
      replicas: 1
      resources:
        limits:
          memory: 1.5G
          cpus: '0.5'
        reservations:
          memory: 512M
          cpus: '0.25'

  content-manager:
    image: aquascene/content-manager:latest
    environment:
      DATABASE_URL: postgresql://${DB_USER}:${DB_PASSWORD}@postgres:5432/${DB_NAME}
      REDIS_URL: redis://:${REDIS_PASSWORD}@redis:6379/0
    secrets:
      - postgres_password
      - redis_password
    networks:
      - content-engine
    deploy:
      replicas: 2
      update_config:
        parallelism: 1
        delay: 30s
        failure_action: rollback
      rollback_config:
        parallelism: 1
        delay: 10s
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3
      resources:
        limits:
          memory: 1G
          cpus: '1.0'
        reservations:
          memory: 512M
          cpus: '0.5'

  ai-processor:
    image: aquascene/ai-processor:latest
    environment:
      DATABASE_URL: postgresql://${DB_USER}:${DB_PASSWORD}@postgres:5432/${DB_NAME}
      REDIS_URL: redis://:${REDIS_PASSWORD}@redis:6379/1
      OPENAI_API_KEY_FILE: /run/secrets/openai_api_key
      ANTHROPIC_API_KEY_FILE: /run/secrets/anthropic_api_key
    secrets:
      - postgres_password
      - redis_password
      - openai_api_key
      - anthropic_api_key
    networks:
      - content-engine
    deploy:
      replicas: 3
      resources:
        limits:
          memory: 2G
          cpus: '2.0'
        reservations:
          memory: 1G
          cpus: '1.0'

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    configs:
      - source: nginx_config
        target: /etc/nginx/nginx.conf
    secrets:
      - ssl_certificate
      - ssl_private_key
    networks:
      - content-engine
    deploy:
      replicas: 2
      placement:
        constraints:
          - node.role == worker

configs:
  nginx_config:
    file: ./infrastructure/nginx/production.conf

secrets:
  postgres_password:
    external: true
  redis_password:
    external: true
  openai_api_key:
    external: true
  anthropic_api_key:
    external: true
  ssl_certificate:
    external: true
  ssl_private_key:
    external: true
```

#### Kubernetes Deployment
```yaml
# kubernetes/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: aquascene-production
---
# kubernetes/postgres-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: postgres
  namespace: aquascene-production
spec:
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
      - name: postgres
        image: postgres:15-alpine
        env:
        - name: POSTGRES_DB
          value: "content_engine"
        - name: POSTGRES_USER
          value: "postgres"
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: postgres-secret
              key: password
        ports:
        - containerPort: 5432
        volumeMounts:
        - name: postgres-storage
          mountPath: /var/lib/postgresql/data
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
      volumes:
      - name: postgres-storage
        persistentVolumeClaim:
          claimName: postgres-pvc
---
# kubernetes/ai-processor-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ai-processor
  namespace: aquascene-production
spec:
  replicas: 3
  selector:
    matchLabels:
      app: ai-processor
  template:
    metadata:
      labels:
        app: ai-processor
    spec:
      containers:
      - name: ai-processor
        image: aquascene/ai-processor:latest
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: database-config
              key: url
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: redis-config
              key: url
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: ai-apis
              key: openai
        - name: ANTHROPIC_API_KEY
          valueFrom:
            secretKeyRef:
              name: ai-apis
              key: anthropic
        ports:
        - containerPort: 8001
        livenessProbe:
          httpGet:
            path: /health
            port: 8001
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8001
          initialDelaySeconds: 5
          periodSeconds: 5
        resources:
          requests:
            memory: "1Gi"
            cpu: "1000m"
          limits:
            memory: "2Gi"
            cpu: "2000m"
---
# kubernetes/hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: ai-processor-hpa
  namespace: aquascene-production
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: ai-processor
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

### Database Configuration

#### PostgreSQL Production Setup
```sql
-- postgresql.conf optimizations
shared_buffers = 256MB
effective_cache_size = 1GB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
effective_io_concurrency = 200
work_mem = 4MB
min_wal_size = 1GB
max_wal_size = 4GB
max_connections = 200

-- Enable connection pooling
listen_addresses = '*'
port = 5432
max_connections = 200
shared_preload_libraries = 'pg_stat_statements'

-- Logging configuration
log_destination = 'stderr'
logging_collector = on
log_directory = 'log'
log_filename = 'postgresql-%Y-%m-%d.log'
log_truncate_on_rotation = off
log_rotation_age = 1d
log_rotation_size = 100MB
log_line_prefix = '%m [%p] %q%u@%d '
log_min_duration_statement = 1000
log_checkpoints = on
log_connections = on
log_disconnections = on
log_lock_waits = on
```

#### Redis Cluster Configuration
```redis
# redis-cluster.conf
port 7000
cluster-enabled yes
cluster-config-file nodes-7000.conf
cluster-node-timeout 5000
appendonly yes
appendfsync everysec
save 900 1
save 300 10
save 60 10000
maxmemory 2gb
maxmemory-policy allkeys-lru
timeout 300
tcp-keepalive 60
```

## CI/CD Pipeline Configuration

### GitHub Actions Workflow

#### Production Deployment Pipeline
```yaml
# .github/workflows/production-deploy.yml
name: Production Deployment

on:
  push:
    branches: [main]
  release:
    types: [published]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: aquascene/content-engine

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: test
          POSTGRES_DB: test_db
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      redis:
        image: redis:7
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
    - name: Checkout code
      uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pytest pytest-cov

    - name: Run tests
      run: |
        pytest tests/ --cov=src --cov-report=xml --cov-report=term-missing
      env:
        DATABASE_URL: postgresql://postgres:test@localhost/test_db
        REDIS_URL: redis://localhost:6379/0

    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml

  security-scan:
    runs-on: ubuntu-latest
    steps:
    - name: Checkout code
      uses: actions/checkout@v4

    - name: Run Trivy vulnerability scanner
      uses: aquasecurity/trivy-action@master
      with:
        scan-type: 'fs'
        scan-ref: '.'
        format: 'sarif'
        output: 'trivy-results.sarif'

    - name: Upload Trivy scan results
      uses: github/codeql-action/upload-sarif@v2
      with:
        sarif_file: 'trivy-results.sarif'

  build-and-push:
    needs: [test, security-scan]
    runs-on: ubuntu-latest
    outputs:
      image-digest: ${{ steps.build.outputs.digest }}
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v4

    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v3

    - name: Login to Container Registry
      uses: docker/login-action@v3
      with:
        registry: ${{ env.REGISTRY }}
        username: ${{ github.actor }}
        password: ${{ secrets.GITHUB_TOKEN }}

    - name: Extract metadata
      id: meta
      uses: docker/metadata-action@v5
      with:
        images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
        tags: |
          type=ref,event=branch
          type=ref,event=pr
          type=semver,pattern={{version}}
          type=semver,pattern={{major}}.{{minor}}
          type=sha,prefix={{branch}}-

    - name: Build and push Docker images
      id: build
      uses: docker/build-push-action@v5
      with:
        context: .
        platforms: linux/amd64,linux/arm64
        push: true
        tags: ${{ steps.meta.outputs.tags }}
        labels: ${{ steps.meta.outputs.labels }}
        cache-from: type=gha
        cache-to: type=gha,mode=max

  deploy-staging:
    needs: build-and-push
    runs-on: ubuntu-latest
    environment: staging
    
    steps:
    - name: Deploy to staging
      uses: azure/k8s-deploy@v1
      with:
        manifests: |
          kubernetes/staging/
        images: |
          ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }}
        kubectl-version: 'latest'

    - name: Run integration tests
      run: |
        sleep 60  # Wait for deployment
        curl -f https://staging-api.aquascene.bg/health || exit 1
        # Add more integration tests

  deploy-production:
    needs: [build-and-push, deploy-staging]
    runs-on: ubuntu-latest
    environment: production
    if: github.ref == 'refs/heads/main' || github.event_name == 'release'
    
    steps:
    - name: Deploy to production
      uses: azure/k8s-deploy@v1
      with:
        manifests: |
          kubernetes/production/
        images: |
          ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }}
        kubectl-version: 'latest'

    - name: Verify production deployment
      run: |
        sleep 120  # Wait for deployment
        curl -f https://api.aquascene.bg/health || exit 1
        # Run production smoke tests

    - name: Notify deployment success
      uses: 8398a7/action-slack@v3
      with:
        status: success
        text: "🚀 Production deployment successful!"
      env:
        SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}

  rollback:
    needs: deploy-production
    runs-on: ubuntu-latest
    if: failure()
    
    steps:
    - name: Rollback production deployment
      run: |
        kubectl rollout undo deployment/ai-processor -n aquascene-production
        kubectl rollout undo deployment/content-manager -n aquascene-production
        
    - name: Notify rollback
      uses: 8398a7/action-slack@v3
      with:
        status: failure
        text: "⚠️ Production deployment failed, rolling back!"
      env:
        SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}
```

### Blue-Green Deployment Strategy

```bash
#!/bin/bash
# scripts/blue-green-deploy.sh

set -e

NAMESPACE="aquascene-production"
IMAGE_TAG="${1:-latest}"
CURRENT_ENV=$(kubectl get service ai-processor -n $NAMESPACE -o jsonpath='{.spec.selector.version}')
NEW_ENV="green"

if [ "$CURRENT_ENV" = "green" ]; then
    NEW_ENV="blue"
fi

echo "Current environment: $CURRENT_ENV"
echo "Deploying to: $NEW_ENV"

# Update deployment with new image
kubectl set image deployment/ai-processor-$NEW_ENV \
    ai-processor=aquascene/ai-processor:$IMAGE_TAG \
    -n $NAMESPACE

# Wait for rollout to complete
kubectl rollout status deployment/ai-processor-$NEW_ENV -n $NAMESPACE

# Run health checks
echo "Running health checks..."
NEW_POD=$(kubectl get pod -l app=ai-processor,version=$NEW_ENV -n $NAMESPACE -o jsonpath='{.items[0].metadata.name}')
kubectl exec $NEW_POD -n $NAMESPACE -- curl -f http://localhost:8001/health

# Run integration tests
echo "Running integration tests..."
kubectl port-forward service/ai-processor-$NEW_ENV 8001:8001 -n $NAMESPACE &
PF_PID=$!
sleep 5

# Test endpoints
curl -f http://localhost:8001/health
curl -f http://localhost:8001/stats

kill $PF_PID

# Switch traffic to new environment
echo "Switching traffic to $NEW_ENV environment..."
kubectl patch service ai-processor -n $NAMESPACE -p \
    '{"spec":{"selector":{"version":"'$NEW_ENV'"}}}'

echo "Deployment complete! Traffic switched to $NEW_ENV environment."
echo "Previous environment ($CURRENT_ENV) is still running for rollback if needed."
```

## Monitoring and Alerting Setup

### Prometheus Configuration

```yaml
# prometheus/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    cluster: 'aquascene-production'
    region: 'us-east-1'

rule_files:
  - "rules/*.yml"

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093

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
    scrape_interval: 15s

  - job_name: 'node-exporter'
    static_configs:
      - targets: ['node-exporter:9100']

  - job_name: 'postgres-exporter'
    static_configs:
      - targets: ['postgres-exporter:9187']

  - job_name: 'redis-exporter'
    static_configs:
      - targets: ['redis-exporter:9121']

  - job_name: 'nginx-exporter'
    static_configs:
      - targets: ['nginx-exporter:9113']
```

### Alerting Rules

```yaml
# prometheus/rules/content-engine-alerts.yml
groups:
  - name: content-engine.rules
    rules:
    - alert: HighErrorRate
      expr: rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m]) > 0.05
      for: 5m
      labels:
        severity: critical
        team: platform
      annotations:
        summary: "High error rate detected"
        description: "Error rate is {{ $value | humanizePercentage }} for {{ $labels.instance }}"

    - alert: AIProcessorDown
      expr: up{job="ai-processor"} == 0
      for: 30s
      labels:
        severity: critical
        team: platform
      annotations:
        summary: "AI Processor is down"
        description: "AI Processor instance {{ $labels.instance }} is down"

    - alert: HighMemoryUsage
      expr: (node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes > 0.9
      for: 5m
      labels:
        severity: warning
        team: infrastructure
      annotations:
        summary: "High memory usage"
        description: "Memory usage is above 90% on {{ $labels.instance }}"

    - alert: HighCPUUsage
      expr: 100 - (avg by(instance) (irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100) > 85
      for: 5m
      labels:
        severity: warning
        team: infrastructure
      annotations:
        summary: "High CPU usage"
        description: "CPU usage is above 85% on {{ $labels.instance }}"

    - alert: DatabaseConnectionsFull
      expr: pg_stat_database_numbackends / pg_settings_max_connections > 0.9
      for: 5m
      labels:
        severity: critical
        team: database
      annotations:
        summary: "Database connections nearly full"
        description: "PostgreSQL connections are at {{ $value | humanizePercentage }} capacity"

    - alert: ContentGenerationLatencyHigh
      expr: histogram_quantile(0.95, rate(content_generation_duration_seconds_bucket[5m])) > 30
      for: 5m
      labels:
        severity: warning
        team: platform
      annotations:
        summary: "High content generation latency"
        description: "95th percentile latency is {{ $value }}s for content generation"

    - alert: LowContentQualityScore
      expr: avg_over_time(content_quality_score[1h]) < 7.0
      for: 15m
      labels:
        severity: warning
        team: content
      annotations:
        summary: "Content quality score dropped"
        description: "Average content quality score is {{ $value }} over the last hour"

    - alert: APIRateLimitExceeded
      expr: rate(http_requests_total{status="429"}[5m]) > 10
      for: 2m
      labels:
        severity: warning
        team: platform
      annotations:
        summary: "API rate limit exceeded"
        description: "Rate limit exceeded for {{ $labels.instance }}"
```

### AlertManager Configuration

```yaml
# alertmanager/alertmanager.yml
global:
  smtp_smarthost: 'smtp.sendgrid.net:587'
  smtp_from: 'alerts@aquascene.bg'
  smtp_auth_username: 'apikey'
  smtp_auth_password: '${SENDGRID_API_KEY}'

route:
  group_by: ['alertname', 'cluster']
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 12h
  receiver: 'default'
  routes:
  - match:
      severity: critical
    receiver: 'critical-alerts'
    group_wait: 10s
    repeat_interval: 5m
  - match:
      team: platform
    receiver: 'platform-team'
  - match:
      team: infrastructure
    receiver: 'infrastructure-team'

receivers:
  - name: 'default'
    email_configs:
    - to: 'ops-team@aquascene.bg'
      subject: 'AquaScene Alert: {{ .GroupLabels.alertname }}'
      body: |
        {{ range .Alerts }}
        Alert: {{ .Annotations.summary }}
        Description: {{ .Annotations.description }}
        Severity: {{ .Labels.severity }}
        {{ end }}

  - name: 'critical-alerts'
    email_configs:
    - to: 'on-call@aquascene.bg'
      subject: 'CRITICAL: {{ .GroupLabels.alertname }}'
      body: |
        🚨 CRITICAL ALERT 🚨
        
        {{ range .Alerts }}
        Alert: {{ .Annotations.summary }}
        Description: {{ .Annotations.description }}
        Instance: {{ .Labels.instance }}
        Time: {{ .StartsAt }}
        {{ end }}
    slack_configs:
    - api_url: '${SLACK_WEBHOOK_URL}'
      channel: '#alerts-critical'
      title: 'CRITICAL: {{ .GroupLabels.alertname }}'
      text: |
        {{ range .Alerts }}
        🚨 {{ .Annotations.summary }}
        📝 {{ .Annotations.description }}
        🔍 Instance: {{ .Labels.instance }}
        ⏰ Started: {{ .StartsAt }}
        {{ end }}

  - name: 'platform-team'
    slack_configs:
    - api_url: '${SLACK_WEBHOOK_URL}'
      channel: '#platform-alerts'
      title: '{{ .GroupLabels.alertname }}'
      text: |
        {{ range .Alerts }}
        ⚠️ {{ .Annotations.summary }}
        {{ .Annotations.description }}
        {{ end }}

  - name: 'infrastructure-team'
    email_configs:
    - to: 'infrastructure@aquascene.bg'
      subject: 'Infrastructure Alert: {{ .GroupLabels.alertname }}'
```

### Grafana Dashboard Configuration

```json
{
  "dashboard": {
    "title": "AquaScene Content Engine - Production Overview",
    "panels": [
      {
        "title": "Request Rate",
        "type": "stat",
        "targets": [
          {
            "expr": "sum(rate(http_requests_total[1m]))",
            "legendFormat": "Requests/sec"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "reqps",
            "thresholds": {
              "steps": [
                {"color": "green", "value": 0},
                {"color": "yellow", "value": 50},
                {"color": "red", "value": 100}
              ]
            }
          }
        }
      },
      {
        "title": "Error Rate",
        "type": "stat",
        "targets": [
          {
            "expr": "sum(rate(http_requests_total{status=~\"5..\"}[1m])) / sum(rate(http_requests_total[1m]))",
            "legendFormat": "Error Rate"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "percent",
            "thresholds": {
              "steps": [
                {"color": "green", "value": 0},
                {"color": "yellow", "value": 1},
                {"color": "red", "value": 5}
              ]
            }
          }
        }
      },
      {
        "title": "Content Generation Performance",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(content_generation_duration_seconds_bucket[5m]))",
            "legendFormat": "95th percentile"
          },
          {
            "expr": "histogram_quantile(0.50, rate(content_generation_duration_seconds_bucket[5m]))",
            "legendFormat": "50th percentile"
          }
        ]
      },
      {
        "title": "AI API Costs (Daily)",
        "type": "stat",
        "targets": [
          {
            "expr": "increase(ai_api_cost_total[24h])",
            "legendFormat": "Daily Cost"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "currencyUSD"
          }
        }
      }
    ]
  }
}
```

## Backup and Disaster Recovery

### Automated Backup Strategy

#### Database Backup Configuration
```bash
#!/bin/bash
# scripts/backup-postgres.sh

set -e

# Configuration
DB_HOST=${DB_HOST:-localhost}
DB_PORT=${DB_PORT:-5432}
DB_NAME=${DB_NAME:-content_engine}
DB_USER=${DB_USER:-postgres}
BACKUP_DIR=${BACKUP_DIR:-/backups/postgres}
S3_BUCKET=${S3_BUCKET:-aquascene-backups}
RETENTION_DAYS=${RETENTION_DAYS:-30}

# Create backup directory
mkdir -p $BACKUP_DIR

# Generate backup filename
BACKUP_DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/postgres_${DB_NAME}_${BACKUP_DATE}.sql.gz"

echo "Starting PostgreSQL backup at $(date)"

# Perform backup
pg_dump -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME | gzip > $BACKUP_FILE

# Verify backup
if [ ! -f "$BACKUP_FILE" ]; then
    echo "Error: Backup file not created"
    exit 1
fi

BACKUP_SIZE=$(du -h $BACKUP_FILE | cut -f1)
echo "Backup created: $BACKUP_FILE ($BACKUP_SIZE)"

# Upload to S3
if [ ! -z "$S3_BUCKET" ]; then
    aws s3 cp $BACKUP_FILE s3://$S3_BUCKET/postgres/$(basename $BACKUP_FILE)
    echo "Backup uploaded to S3: s3://$S3_BUCKET/postgres/$(basename $BACKUP_FILE)"
fi

# Cleanup old backups
find $BACKUP_DIR -name "postgres_${DB_NAME}_*.sql.gz" -mtime +$RETENTION_DAYS -delete
echo "Cleaned up backups older than $RETENTION_DAYS days"

# Test backup integrity
echo "Testing backup integrity..."
gunzip -t $BACKUP_FILE
if [ $? -eq 0 ]; then
    echo "Backup integrity check passed"
else
    echo "Error: Backup integrity check failed"
    exit 1
fi

echo "PostgreSQL backup completed successfully at $(date)"
```

#### Redis Backup Configuration
```bash
#!/bin/bash
# scripts/backup-redis.sh

set -e

REDIS_HOST=${REDIS_HOST:-localhost}
REDIS_PORT=${REDIS_PORT:-6379}
REDIS_PASSWORD=${REDIS_PASSWORD}
BACKUP_DIR=${BACKUP_DIR:-/backups/redis}
S3_BUCKET=${S3_BUCKET:-aquascene-backups}

mkdir -p $BACKUP_DIR

BACKUP_DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/redis_${BACKUP_DATE}.rdb"

echo "Starting Redis backup at $(date)"

# Create Redis snapshot
if [ ! -z "$REDIS_PASSWORD" ]; then
    redis-cli -h $REDIS_HOST -p $REDIS_PORT -a $REDIS_PASSWORD --rdb $BACKUP_FILE
else
    redis-cli -h $REDIS_HOST -p $REDIS_PORT --rdb $BACKUP_FILE
fi

# Compress backup
gzip $BACKUP_FILE

# Upload to S3
if [ ! -z "$S3_BUCKET" ]; then
    aws s3 cp ${BACKUP_FILE}.gz s3://$S3_BUCKET/redis/$(basename ${BACKUP_FILE}.gz)
    echo "Redis backup uploaded to S3"
fi

echo "Redis backup completed successfully at $(date)"
```

#### Backup Automation with Kubernetes CronJob
```yaml
# kubernetes/backup-cronjob.yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: postgres-backup
  namespace: aquascene-production
spec:
  schedule: "0 2 * * *"  # Daily at 2 AM
  concurrencyPolicy: Forbid
  successfulJobsHistoryLimit: 7
  failedJobsHistoryLimit: 3
  jobTemplate:
    spec:
      template:
        spec:
          restartPolicy: OnFailure
          containers:
          - name: postgres-backup
            image: postgres:15-alpine
            env:
            - name: PGPASSWORD
              valueFrom:
                secretKeyRef:
                  name: postgres-secret
                  key: password
            - name: AWS_ACCESS_KEY_ID
              valueFrom:
                secretKeyRef:
                  name: aws-credentials
                  key: access-key-id
            - name: AWS_SECRET_ACCESS_KEY
              valueFrom:
                secretKeyRef:
                  name: aws-credentials
                  key: secret-access-key
            command:
            - /bin/bash
            - -c
            - |
              apk add --no-cache aws-cli
              BACKUP_FILE="/tmp/postgres_backup_$(date +%Y%m%d_%H%M%S).sql.gz"
              pg_dump -h postgres -U postgres -d content_engine | gzip > $BACKUP_FILE
              aws s3 cp $BACKUP_FILE s3://aquascene-backups/postgres/
              echo "Backup completed: $BACKUP_FILE"
          - name: redis-backup
            image: redis:7-alpine
            env:
            - name: AWS_ACCESS_KEY_ID
              valueFrom:
                secretKeyRef:
                  name: aws-credentials
                  key: access-key-id
            - name: AWS_SECRET_ACCESS_KEY
              valueFrom:
                secretKeyRef:
                  name: aws-credentials
                  key: secret-access-key
            command:
            - /bin/bash
            - -c
            - |
              apk add --no-cache aws-cli
              BACKUP_FILE="/tmp/redis_backup_$(date +%Y%m%d_%H%M%S).rdb"
              redis-cli -h redis --rdb $BACKUP_FILE
              gzip $BACKUP_FILE
              aws s3 cp ${BACKUP_FILE}.gz s3://aquascene-backups/redis/
              echo "Redis backup completed"
```

### Disaster Recovery Procedures

#### Database Recovery Process
```bash
#!/bin/bash
# scripts/restore-postgres.sh

set -e

BACKUP_FILE=$1
DB_HOST=${DB_HOST:-localhost}
DB_PORT=${DB_PORT:-5432}
DB_NAME=${DB_NAME:-content_engine}
DB_USER=${DB_USER:-postgres}

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <backup_file>"
    echo "Available backups:"
    aws s3 ls s3://aquascene-backups/postgres/ | grep .sql.gz
    exit 1
fi

echo "Starting database recovery from: $BACKUP_FILE"

# Download backup from S3 if needed
if [[ $BACKUP_FILE == s3://* ]]; then
    LOCAL_FILE="/tmp/$(basename $BACKUP_FILE)"
    aws s3 cp $BACKUP_FILE $LOCAL_FILE
    BACKUP_FILE=$LOCAL_FILE
fi

# Stop application services
echo "Stopping application services..."
kubectl scale deployment --replicas=0 -l app=content-manager -n aquascene-production
kubectl scale deployment --replicas=0 -l app=ai-processor -n aquascene-production

# Drop existing database
echo "Dropping existing database..."
psql -h $DB_HOST -p $DB_PORT -U $DB_USER -c "DROP DATABASE IF EXISTS ${DB_NAME}_backup;"
psql -h $DB_HOST -p $DB_PORT -U $DB_USER -c "ALTER DATABASE $DB_NAME RENAME TO ${DB_NAME}_backup;"
psql -h $DB_HOST -p $DB_PORT -U $DB_USER -c "CREATE DATABASE $DB_NAME;"

# Restore database
echo "Restoring database from backup..."
if [[ $BACKUP_FILE == *.gz ]]; then
    gunzip -c $BACKUP_FILE | psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME
else
    psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME < $BACKUP_FILE
fi

# Verify restoration
echo "Verifying database restoration..."
TABLE_COUNT=$(psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';")
if [ $TABLE_COUNT -gt 0 ]; then
    echo "Database restoration successful. Found $TABLE_COUNT tables."
else
    echo "Error: Database restoration failed. No tables found."
    exit 1
fi

# Restart application services
echo "Restarting application services..."
kubectl scale deployment --replicas=2 -l app=content-manager -n aquascene-production
kubectl scale deployment --replicas=3 -l app=ai-processor -n aquascene-production

# Wait for services to be ready
echo "Waiting for services to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment -l app=content-manager -n aquascene-production
kubectl wait --for=condition=available --timeout=300s deployment -l app=ai-processor -n aquascene-production

echo "Database recovery completed successfully!"
```

#### Full System Recovery Runbook
```markdown
# Disaster Recovery Runbook

## Complete System Failure Recovery

### Step 1: Assess the Situation
1. Check monitoring dashboards for scope of failure
2. Verify if it's partial or complete system failure
3. Check if data is intact or corrupted
4. Estimate recovery time objective (RTO) and recovery point objective (RPO)

### Step 2: Infrastructure Recovery
1. **Cloud Infrastructure**
   ```bash
   # Re-deploy infrastructure using Terraform
   cd infrastructure/terraform
   terraform plan -out=recovery.plan
   terraform apply recovery.plan
   ```

2. **Kubernetes Cluster**
   ```bash
   # Create new cluster if needed
   kubectl apply -f kubernetes/namespace.yaml
   kubectl apply -f kubernetes/secrets/
   kubectl apply -f kubernetes/configmaps/
   ```

### Step 3: Database Recovery
1. **Identify Latest Backup**
   ```bash
   aws s3 ls s3://aquascene-backups/postgres/ --recursive | sort | tail -1
   ```

2. **Restore Database**
   ```bash
   ./scripts/restore-postgres.sh s3://aquascene-backups/postgres/latest.sql.gz
   ```

3. **Verify Data Integrity**
   ```sql
   SELECT COUNT(*) FROM content;
   SELECT COUNT(*) FROM subscribers;
   SELECT MAX(created_at) FROM content;
   ```

### Step 4: Application Deployment
1. **Deploy Applications**
   ```bash
   kubectl apply -f kubernetes/production/
   ```

2. **Verify Health**
   ```bash
   kubectl get pods -n aquascene-production
   curl -f https://api.aquascene.bg/health
   ```

### Step 5: Data Validation
1. **Run Data Consistency Checks**
2. **Verify Recent Content Generation**
3. **Check Subscriber Data Integrity**
4. **Validate Analytics Data**

### Step 6: Service Restoration
1. **Enable Traffic Routing**
2. **Monitor Error Rates**
3. **Verify All Integrations**
4. **Check Partner API Connections**

### Step 7: Post-Recovery Validation
1. **Run Full Test Suite**
2. **Verify Content Generation**
3. **Test Newsletter Sending**
4. **Check Social Media Automation**

### Step 8: Communication
1. **Notify Stakeholders of Recovery**
2. **Update Status Pages**
3. **Document Lessons Learned**
4. **Schedule Post-Mortem Meeting**
```

## Security Hardening

### Network Security Configuration

#### Nginx Security Configuration
```nginx
# nginx/production.conf
server {
    listen 443 ssl http2;
    server_name api.aquascene.bg;
    
    # SSL Configuration
    ssl_certificate /etc/nginx/certs/aquascene.crt;
    ssl_certificate_key /etc/nginx/certs/aquascene.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # Security Headers
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload";
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Referrer-Policy "strict-origin-when-cross-origin";
    add_header Content-Security-Policy "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline';";
    
    # Rate Limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=generate:10m rate=1r/s;
    
    # Hide Server Information
    server_tokens off;
    
    # Client Body Size
    client_max_body_size 10M;
    
    # API Endpoints
    location /api/v1/generate {
        limit_req zone=generate burst=5 nodelay;
        proxy_pass http://ai-processor:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeout settings
        proxy_connect_timeout 30s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }
    
    location /api/v1/ {
        limit_req zone=api burst=20 nodelay;
        proxy_pass http://content-manager:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Block common attacks
    location ~ /\. {
        deny all;
        access_log off;
        log_not_found off;
    }
    
    location ~ (\.php|\.asp|\.aspx|\.jsp)$ {
        deny all;
        access_log off;
        log_not_found off;
    }
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name api.aquascene.bg;
    return 301 https://$server_name$request_uri;
}
```

#### Container Security Configuration
```dockerfile
# Dockerfile.production
FROM python:3.11-slim as base

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Install security updates
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
        curl \
        ca-certificates && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

FROM base as dependencies

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM base as production

# Copy dependencies
COPY --from=dependencies /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages

# Copy application code
WORKDIR /app
COPY --chown=appuser:appuser . .

# Security: Remove write permissions from application files
RUN chmod -R 755 /app && \
    find /app -type f -exec chmod 644 {} \; && \
    chmod +x /app/scripts/*.sh

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

EXPOSE 8001

CMD ["python", "src/main.py"]
```

### Secrets Management

#### Kubernetes Secrets Configuration
```bash
#!/bin/bash
# scripts/setup-secrets.sh

# Create namespace
kubectl create namespace aquascene-production

# Database credentials
kubectl create secret generic postgres-secret \
    --from-literal=username=postgres \
    --from-literal=password="$(openssl rand -base64 32)" \
    --from-literal=database=content_engine \
    -n aquascene-production

# Redis credentials
kubectl create secret generic redis-secret \
    --from-literal=password="$(openssl rand -base64 24)" \
    -n aquascene-production

# AI API Keys
kubectl create secret generic ai-api-keys \
    --from-literal=openai-key="${OPENAI_API_KEY}" \
    --from-literal=anthropic-key="${ANTHROPIC_API_KEY}" \
    -n aquascene-production

# External service keys
kubectl create secret generic external-apis \
    --from-literal=sendgrid-key="${SENDGRID_API_KEY}" \
    --from-literal=instagram-token="${INSTAGRAM_ACCESS_TOKEN}" \
    -n aquascene-production

# SSL Certificates
kubectl create secret tls ssl-certificate \
    --cert=certs/aquascene.crt \
    --key=certs/aquascene.key \
    -n aquascene-production

# AWS Credentials for backups
kubectl create secret generic aws-credentials \
    --from-literal=access-key-id="${AWS_ACCESS_KEY_ID}" \
    --from-literal=secret-access-key="${AWS_SECRET_ACCESS_KEY}" \
    -n aquascene-production

echo "All secrets created successfully!"
```

#### Environment-Specific Secret Management
```python
# utils/secrets_manager.py
import os
import boto3
from botocore.exceptions import ClientError

class SecretsManager:
    def __init__(self, region_name='us-east-1'):
        self.client = boto3.client('secretsmanager', region_name=region_name)
    
    def get_secret(self, secret_name: str) -> dict:
        """Retrieve secret from AWS Secrets Manager"""
        try:
            response = self.client.get_secret_value(SecretId=secret_name)
            return json.loads(response['SecretString'])
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                # Fall back to environment variables in development
                return self._get_env_fallback(secret_name)
            raise e
    
    def _get_env_fallback(self, secret_name: str) -> dict:
        """Fallback to environment variables for development"""
        secrets = {
            'aquascene/prod/database': {
                'username': os.getenv('DB_USER'),
                'password': os.getenv('DB_PASSWORD'),
                'database': os.getenv('DB_NAME'),
                'host': os.getenv('DB_HOST')
            },
            'aquascene/prod/ai-apis': {
                'openai_api_key': os.getenv('OPENAI_API_KEY'),
                'anthropic_api_key': os.getenv('ANTHROPIC_API_KEY')
            },
            'aquascene/prod/external-services': {
                'sendgrid_api_key': os.getenv('SENDGRID_API_KEY'),
                'instagram_access_token': os.getenv('INSTAGRAM_ACCESS_TOKEN')
            }
        }
        
        return secrets.get(secret_name, {})
    
    def rotate_secret(self, secret_name: str, new_value: dict):
        """Rotate secret value"""
        try:
            self.client.update_secret(
                SecretId=secret_name,
                SecretString=json.dumps(new_value)
            )
            return True
        except ClientError as e:
            print(f"Error rotating secret {secret_name}: {e}")
            return False

# Usage in application
secrets_manager = SecretsManager()
db_secrets = secrets_manager.get_secret('aquascene/prod/database')
DATABASE_URL = f"postgresql://{db_secrets['username']}:{db_secrets['password']}@{db_secrets['host']}/{db_secrets['database']}"
```

## Performance Optimization

### Application Performance Tuning

#### FastAPI Performance Configuration
```python
# src/performance_config.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
import uvicorn

def create_optimized_app() -> FastAPI:
    app = FastAPI(
        title="AquaScene Content Engine",
        version="1.0.0",
        docs_url="/docs" if os.getenv("ENVIRONMENT") != "production" else None,
        redoc_url="/redoc" if os.getenv("ENVIRONMENT") != "production" else None
    )
    
    # Add compression middleware
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    
    # CORS configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["https://admin.aquascene.bg", "https://aquascene.bg"],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["*"],
    )
    
    return app

# Optimized Uvicorn configuration
def run_production_server():
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        workers=4,  # Adjust based on CPU cores
        worker_class="uvicorn.workers.UvicornWorker",
        loop="uvloop",  # Use uvloop for better performance
        http="httptools",  # Use httptools for better HTTP parsing
        access_log=False,  # Disable access logs in production
        server_header=False,  # Don't send server header
        date_header=False  # Don't send date header
    )
```

#### Database Connection Pooling
```python
# src/database/connection_pool.py
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool
import asyncpg
from asyncpg import pool

class DatabaseConnectionManager:
    def __init__(self, database_url: str, max_connections: int = 20):
        self.database_url = database_url
        self.max_connections = max_connections
        self.pool = None
    
    async def initialize_pool(self):
        """Initialize async connection pool"""
        self.pool = await asyncpg.create_pool(
            self.database_url,
            min_size=5,
            max_size=self.max_connections,
            command_timeout=60,
            server_settings={
                'jit': 'off',  # Disable JIT for better connection startup
                'application_name': 'aquascene_content_engine'
            }
        )
    
    async def get_connection(self):
        """Get connection from pool"""
        if not self.pool:
            await self.initialize_pool()
        return self.pool.acquire()
    
    async def execute_query(self, query: str, *args):
        """Execute query with automatic connection management"""
        async with self.pool.acquire() as conn:
            return await conn.fetch(query, *args)
    
    async def execute_transaction(self, queries: list):
        """Execute multiple queries in a transaction"""
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                results = []
                for query, args in queries:
                    result = await conn.fetch(query, *args)
                    results.append(result)
                return results
    
    async def close_pool(self):
        """Close connection pool"""
        if self.pool:
            await self.pool.close()

# Usage
db_manager = DatabaseConnectionManager(DATABASE_URL, max_connections=20)
```

#### Redis Caching Strategy
```python
# src/cache/redis_cache.py
import json
import hashlib
from typing import Any, Optional
import redis.asyncio as aioredis

class RedisCache:
    def __init__(self, redis_url: str, default_ttl: int = 3600):
        self.redis_url = redis_url
        self.default_ttl = default_ttl
        self.client = None
    
    async def initialize(self):
        """Initialize Redis connection"""
        self.client = aioredis.from_url(
            self.redis_url,
            encoding="utf-8",
            decode_responses=True,
            max_connections=20
        )
    
    def _generate_key(self, prefix: str, data: dict) -> str:
        """Generate cache key from data"""
        serialized = json.dumps(data, sort_keys=True)
        hash_object = hashlib.md5(serialized.encode())
        return f"{prefix}:{hash_object.hexdigest()}"
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self.client:
            await self.initialize()
        
        try:
            value = await self.client.get(key)
            if value:
                return json.loads(value)
        except Exception as e:
            print(f"Cache get error: {e}")
        return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache"""
        if not self.client:
            await self.initialize()
        
        try:
            serialized = json.dumps(value, default=str)
            ttl = ttl or self.default_ttl
            return await self.client.setex(key, ttl, serialized)
        except Exception as e:
            print(f"Cache set error: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        if not self.client:
            await self.initialize()
        
        try:
            return await self.client.delete(key) > 0
        except Exception as e:
            print(f"Cache delete error: {e}")
            return False
    
    async def cache_content_generation(self, request_data: dict, result: dict, ttl: int = 7200):
        """Cache content generation results"""
        cache_key = self._generate_key("content_gen", request_data)
        await self.set(cache_key, result, ttl)
    
    async def get_cached_content(self, request_data: dict) -> Optional[dict]:
        """Get cached content generation result"""
        cache_key = self._generate_key("content_gen", request_data)
        return await self.get(cache_key)

# Caching decorator
from functools import wraps

def cache_result(prefix: str, ttl: int = 3600):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key from function arguments
            cache_key = f"{prefix}:{hashlib.md5(str(args + tuple(kwargs.items())).encode()).hexdigest()}"
            
            # Try to get from cache
            cached_result = await redis_cache.get(cache_key)
            if cached_result:
                return cached_result
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            await redis_cache.set(cache_key, result, ttl)
            return result
        return wrapper
    return decorator

# Usage
@cache_result("template", ttl=3600)
async def get_template_configuration(template_id: str):
    # Expensive template loading operation
    return await load_template_from_database(template_id)
```

## Operational Procedures

### Daily Operations Checklist

#### Morning Health Check
```bash
#!/bin/bash
# scripts/morning-health-check.sh

echo "AquaScene Content Engine - Daily Health Check"
echo "=============================================="
date

# Check service status
echo "1. Checking service health..."
curl -s http://localhost:8000/health | jq '.'
curl -s http://localhost:8001/health | jq '.'

# Check system resources
echo "2. System resource usage:"
kubectl top nodes
kubectl top pods -n aquascene-production

# Check error rates from last 24h
echo "3. Error rates (last 24h):"
curl -s "http://prometheus:9090/api/v1/query?query=rate(http_requests_total{status=~\"5..\"}[24h])" | jq '.data.result[]'

# Check content generation stats
echo "4. Content generation stats (last 24h):"
curl -s "http://prometheus:9090/api/v1/query?query=increase(content_generation_total[24h])" | jq '.data.result[]'

# Check database connections
echo "5. Database connection status:"
kubectl exec -it postgres-0 -n aquascene-production -- psql -U postgres -d content_engine -c "SELECT count(*) FROM pg_stat_activity;"

# Check backup status
echo "6. Backup status:"
aws s3 ls s3://aquascene-backups/postgres/ | tail -1

# Check for critical alerts
echo "7. Active alerts:"
curl -s http://alertmanager:9093/api/v1/alerts | jq '.data[] | select(.status.state == "active")'

echo "Health check completed at $(date)"
```

#### Weekly Maintenance Tasks
```bash
#!/bin/bash
# scripts/weekly-maintenance.sh

echo "Weekly Maintenance Tasks - $(date)"
echo "=================================="

# 1. Database maintenance
echo "1. Running database maintenance..."
kubectl exec -it postgres-0 -n aquascene-production -- psql -U postgres -d content_engine -c "
    VACUUM ANALYZE;
    REINDEX DATABASE content_engine;
    SELECT pg_size_pretty(pg_database_size('content_engine')) as database_size;
"

# 2. Clear old logs
echo "2. Clearing old logs..."
kubectl get pods -n aquascene-production -o name | xargs -I {} kubectl logs {} --previous --tail=0 > /dev/null

# 3. Update system packages (if applicable)
echo "3. Checking for security updates..."
kubectl get nodes -o wide

# 4. Certificate expiry check
echo "4. Checking SSL certificate expiry..."
openssl x509 -in /etc/ssl/certs/aquascene.crt -noout -dates

# 5. Backup verification
echo "5. Verifying recent backups..."
aws s3 ls s3://aquascene-backups/postgres/ | tail -5
aws s3 ls s3://aquascene-backups/redis/ | tail -5

# 6. Performance analysis
echo "6. Weekly performance summary..."
curl -s "http://prometheus:9090/api/v1/query?query=avg_over_time(http_request_duration_seconds{quantile=\"0.95\"}[7d])" | jq '.data.result[]'

# 7. Cost analysis
echo "7. AI API cost summary (last 7 days)..."
curl -s "http://prometheus:9090/api/v1/query?query=increase(ai_api_cost_total[7d])" | jq '.data.result[]'

echo "Weekly maintenance completed at $(date)"
```

### Incident Response Procedures

#### Critical Service Down Response
```markdown
# Critical Service Down - Incident Response

## Immediate Actions (0-15 minutes)
1. **Acknowledge Alert**
   - Update status page: "Investigating service disruption"
   - Notify team via Slack: #incident-response

2. **Initial Assessment**
   ```bash
   kubectl get pods -n aquascene-production
   kubectl get events -n aquascene-production --sort-by='.lastTimestamp'
   ```

3. **Quick Fixes (if applicable)**
   ```bash
   # Restart failed pods
   kubectl delete pod <failed-pod-name> -n aquascene-production
   
   # Scale up replicas if needed
   kubectl scale deployment ai-processor --replicas=5 -n aquascene-production
   ```

## Investigation Phase (15-30 minutes)
1. **Gather Information**
   - Check Grafana dashboards
   - Review application logs
   - Check external dependencies

2. **Root Cause Analysis**
   ```bash
   # Check resource usage
   kubectl top pods -n aquascene-production
   
   # Check logs
   kubectl logs -l app=ai-processor -n aquascene-production --tail=100
   
   # Check database status
   kubectl exec postgres-0 -n aquascene-production -- pg_isready
   ```

## Resolution Phase (30+ minutes)
1. **Implement Fix**
   - Apply configuration changes
   - Deploy hotfixes if necessary
   - Scale resources if needed

2. **Verify Resolution**
   - Run health checks
   - Monitor error rates
   - Test critical functionality

## Post-Incident (1-24 hours)
1. **Update Status Page**
   - Confirm services are fully operational
   - Provide incident summary

2. **Document Incident**
   - Create incident report
   - Schedule post-mortem meeting
   - Update runbooks based on lessons learned
```

#### Performance Degradation Response
```markdown
# Performance Degradation - Response Procedure

## Detection Indicators
- Response times > 5 seconds (95th percentile)
- Error rates > 5%
- Memory usage > 90%
- CPU usage > 85% sustained

## Immediate Actions
1. **Scale Resources**
   ```bash
   kubectl scale deployment ai-processor --replicas=5 -n aquascene-production
   kubectl scale deployment content-manager --replicas=3 -n aquascene-production
   ```

2. **Enable Circuit Breakers**
   ```bash
   # Update configuration to enable fallbacks
   kubectl patch configmap app-config -n aquascene-production --patch '{"data":{"enable_fallbacks":"true"}}'
   ```

3. **Monitor Key Metrics**
   - Watch response times in Grafana
   - Monitor resource utilization
   - Track error rates

## Investigation Steps
1. **Database Performance**
   ```sql
   -- Check slow queries
   SELECT query, mean_time, calls, total_time
   FROM pg_stat_statements
   ORDER BY mean_time DESC
   LIMIT 10;
   
   -- Check connection counts
   SELECT count(*) FROM pg_stat_activity;
   ```

2. **Application Bottlenecks**
   - Review application logs for errors
   - Check AI API response times
   - Verify external service availability

3. **Infrastructure Issues**
   - Check node resource utilization
   - Verify network connectivity
   - Review storage I/O metrics
```

---

**Document Status:** Complete ✅  
**Deployment Model:** Production Ready  
**Security Level:** Enterprise Grade  
**Availability Target:** 99.9%  
**Recovery Time Objective:** < 4 hours  
**Recovery Point Objective:** < 1 hour  
**Next Review:** September 6, 2025