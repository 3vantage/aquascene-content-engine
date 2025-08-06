# AquaScene Content Engine - Deployment Architecture

## Table of Contents
1. [Deployment Overview](#deployment-overview)
2. [Environment Strategy](#environment-strategy)
3. [Container Orchestration](#container-orchestration)
4. [CI/CD Pipeline](#cicd-pipeline)
5. [Configuration Management](#configuration-management)
6. [Service Deployment Patterns](#service-deployment-patterns)
7. [Database Deployment](#database-deployment)
8. [Monitoring and Logging Deployment](#monitoring-and-logging-deployment)
9. [High Availability Deployment](#high-availability-deployment)
10. [Disaster Recovery and Backup](#disaster-recovery-and-backup)

## Deployment Overview

The AquaScene Content Engine is designed with deployment flexibility in mind, supporting multiple deployment strategies from local development to cloud-native production environments.

### Deployment Architecture Diagram
```mermaid
graph TB
    subgraph "Development Environment"
        DEV[Docker Compose<br/>Single Host]
        DEV_DB[(Local PostgreSQL)]
        DEV_CACHE[(Local Redis)]
    end
    
    subgraph "Staging Environment"
        STAGE_LB[Load Balancer]
        STAGE_APPS[Application Services<br/>Docker Swarm]
        STAGE_DB[(PostgreSQL Primary)]
        STAGE_DB_REPLICA[(PostgreSQL Replica)]
        STAGE_CACHE[(Redis Cluster)]
        STAGE_STORAGE[(MinIO Cluster)]
    end
    
    subgraph "Production Environment"
        PROD_CDN[CDN]
        PROD_LB[Load Balancer<br/>Multiple Zones]
        
        subgraph "Kubernetes Cluster"
            PROD_INGRESS[Ingress Controller]
            PROD_SERVICES[Microservices<br/>Pods]
            PROD_MONITORING[Monitoring Stack]
        end
        
        subgraph "Data Layer"
            PROD_DB[(PostgreSQL HA<br/>Multi-Zone)]
            PROD_CACHE[(Redis HA<br/>Multi-Zone)]
            PROD_STORAGE[(Object Storage<br/>Multi-Zone)]
        end
        
        subgraph "External Services"
            BACKUP[Backup Storage]
            LOGS[Log Aggregation]
            METRICS[Metrics Storage]
        end
    end
    
    DEV --> STAGE_LB
    STAGE_LB --> STAGE_APPS
    STAGE_APPS --> STAGE_DB
    STAGE_APPS --> STAGE_DB_REPLICA
    STAGE_APPS --> STAGE_CACHE
    STAGE_APPS --> STAGE_STORAGE
    
    STAGE_APPS --> PROD_CDN
    PROD_CDN --> PROD_LB
    PROD_LB --> PROD_INGRESS
    PROD_INGRESS --> PROD_SERVICES
    PROD_SERVICES --> PROD_DB
    PROD_SERVICES --> PROD_CACHE
    PROD_SERVICES --> PROD_STORAGE
    PROD_SERVICES --> PROD_MONITORING
    
    PROD_DB --> BACKUP
    PROD_SERVICES --> LOGS
    PROD_MONITORING --> METRICS
```

### Deployment Targets
```yaml
Development:
  Platform: Docker Compose
  Host: Single developer machine
  Purpose: Local development and testing
  Complexity: Minimal
  
Staging:
  Platform: Docker Swarm / Docker Compose
  Host: Single server or small cluster
  Purpose: Integration testing, UAT
  Complexity: Medium
  
Production:
  Platform: Kubernetes / Docker Swarm
  Host: Multi-node cluster, multi-zone
  Purpose: Production workloads
  Complexity: High
  
Edge/Demo:
  Platform: Single container / Docker Compose
  Host: Edge devices, demo environments
  Purpose: Demos, POCs, lightweight deployments
  Complexity: Minimal
```

## Environment Strategy

### Environment Configuration Matrix
```yaml
Development:
  Infrastructure:
    Containers: Docker Compose
    Networking: Bridge networks
    Storage: Local volumes
    Database: Single PostgreSQL instance
    Cache: Single Redis instance
    Monitoring: Basic Prometheus + Grafana
    
  Configuration:
    Debug: Enabled
    Hot Reload: Enabled
    SSL: Disabled (HTTP only)
    Log Level: DEBUG
    External APIs: Sandbox/mock endpoints
    Database Pool Size: 5
    
  Resource Allocation:
    CPU Limits: Unlimited
    Memory Limits: Generous (2GB per service)
    Storage: Local filesystem
    Backup: Optional
    
Staging:
  Infrastructure:
    Containers: Docker Swarm or Kubernetes
    Networking: Overlay networks
    Storage: Network volumes
    Database: PostgreSQL with read replica
    Cache: Redis with persistence
    Monitoring: Full stack with alerting
    
  Configuration:
    Debug: Limited
    Hot Reload: Disabled
    SSL: Let's Encrypt certificates
    Log Level: INFO
    External APIs: Production endpoints (limited)
    Database Pool Size: 15
    
  Resource Allocation:
    CPU Limits: Production-like
    Memory Limits: Production-like (1GB per service)
    Storage: Network-attached storage
    Backup: Daily backups
    
Production:
  Infrastructure:
    Containers: Kubernetes with HA
    Networking: CNI (Calico/Flannel)
    Storage: Persistent volumes (SSD)
    Database: PostgreSQL cluster with failover
    Cache: Redis cluster with HA
    Monitoring: Enterprise monitoring with SLA alerting
    
  Configuration:
    Debug: Disabled
    Hot Reload: Disabled
    SSL: Production certificates
    Log Level: WARN/ERROR
    External APIs: Production endpoints
    Database Pool Size: 25
    
  Resource Allocation:
    CPU Limits: Strict limits with HPA
    Memory Limits: Optimized (512MB-1GB per service)
    Storage: High-performance persistent storage
    Backup: Continuous backup with PITR
```

### Environment Promotion Strategy
```mermaid
graph LR
    DEV[Development<br/>Feature Branch] --> PR[Pull Request<br/>Code Review]
    PR --> STAGE[Staging<br/>Integration Tests]
    STAGE --> PROD_READY[Production Ready<br/>Release Branch]
    PROD_READY --> PROD[Production<br/>Blue-Green Deploy]
    
    STAGE --> ROLLBACK1[Rollback to Dev]
    PROD --> ROLLBACK2[Rollback to Previous]
```

## Container Orchestration

### Docker Compose (Development)
```yaml
# docker-compose.yml - Development Configuration
version: '3.8'

x-common-variables: &common-variables
  ENVIRONMENT: development
  DATABASE_URL: postgresql://postgres:${DB_PASSWORD}@postgres:5432/content_engine
  REDIS_URL: redis://:${REDIS_PASSWORD}@redis:6379
  LOG_LEVEL: DEBUG

x-resource-limits: &resource-limits
  deploy:
    resources:
      limits:
        memory: 1G
        cpus: '1.0'
      reservations:
        memory: 256M
        cpus: '0.25'

services:
  # Application Services
  content-manager:
    build:
      context: ./services/content-manager
      target: development
    environment:
      <<: *common-variables
      SERVICE_NAME: content-manager
    <<: *resource-limits
    volumes:
      - ./services/content-manager:/app
      - ./shared:/app/shared:ro
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy

  # Infrastructure Services
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: content_engine
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./infrastructure/database/init:/docker-entrypoint-initdb.d:ro
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres -d content_engine"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
  redis_data:
  minio_data:

networks:
  content-engine:
    driver: bridge
```

### Docker Swarm (Staging)
```yaml
# docker-compose.staging.yml - Docker Swarm Configuration
version: '3.8'

services:
  content-manager:
    image: aquascene/content-manager:${VERSION}
    deploy:
      replicas: 2
      update_config:
        parallelism: 1
        delay: 10s
        order: start-first
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3
      resources:
        limits:
          memory: 1G
          cpus: '0.5'
        reservations:
          memory: 512M
          cpus: '0.25'
      placement:
        constraints:
          - node.role == worker
    environment:
      ENVIRONMENT: staging
    networks:
      - content-engine
      - traefik
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.content-manager.rule=PathPrefix(`/api`)"
      - "traefik.http.services.content-manager.loadbalancer.server.port=8000"

  postgres:
    image: postgres:15
    deploy:
      replicas: 1
      placement:
        constraints:
          - node.labels.database == true
      resources:
        limits:
          memory: 4G
          cpus: '2.0'
    environment:
      POSTGRES_DB: content_engine
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD_FILE: /run/secrets/db_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - content-engine
    secrets:
      - db_password

secrets:
  db_password:
    external: true

networks:
  content-engine:
    driver: overlay
    attachable: true
  traefik:
    external: true

volumes:
  postgres_data:
    driver: local
```

### Kubernetes (Production)
```yaml
# kubernetes/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: aquascene-content-engine
  labels:
    name: aquascene-content-engine
    environment: production

---
# kubernetes/content-manager-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: content-manager
  namespace: aquascene-content-engine
  labels:
    app: content-manager
    version: v1
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels:
      app: content-manager
  template:
    metadata:
      labels:
        app: content-manager
        version: v1
    spec:
      securityContext:
        runAsNonRoot: true
        runAsUser: 10001
        fsGroup: 10001
      containers:
      - name: content-manager
        image: aquascene/content-manager:${VERSION}
        ports:
        - containerPort: 8000
          name: http
        env:
        - name: ENVIRONMENT
          value: "production"
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: database-secrets
              key: url
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: redis-secrets
              key: url
        resources:
          requests:
            memory: "256Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 3
        volumeMounts:
        - name: config
          mountPath: /app/config
          readOnly: true
        - name: shared
          mountPath: /app/shared
          readOnly: true
      volumes:
      - name: config
        configMap:
          name: content-manager-config
      - name: shared
        persistentVolumeClaim:
          claimName: shared-storage

---
# kubernetes/content-manager-service.yaml
apiVersion: v1
kind: Service
metadata:
  name: content-manager
  namespace: aquascene-content-engine
  labels:
    app: content-manager
spec:
  type: ClusterIP
  ports:
  - port: 8000
    targetPort: 8000
    name: http
  selector:
    app: content-manager

---
# kubernetes/content-manager-hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: content-manager-hpa
  namespace: aquascene-content-engine
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: content-manager
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
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 100
        periodSeconds: 15
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 10
        periodSeconds: 60
```

## CI/CD Pipeline

### GitHub Actions Workflow
```yaml
# .github/workflows/deploy.yml
name: Build and Deploy

on:
  push:
    branches: [ main, develop, staging ]
  pull_request:
    branches: [ main ]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: content_engine_test
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
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r services/content-manager/requirements.txt
        pip install pytest pytest-asyncio pytest-cov
    
    - name: Run tests
      run: |
        pytest services/content-manager/tests/ -v --cov=src
        pytest services/ai-processor/tests/ -v --cov=src
        pytest services/web-scraper/tests/ -v --cov=src
        pytest services/distributor/tests/ -v --cov=src
        pytest services/subscriber-manager/tests/ -v --cov=src
      env:
        DATABASE_URL: postgresql://postgres:postgres@localhost/content_engine_test
        REDIS_URL: redis://localhost:6379
    
    - name: Run integration tests
      run: |
        docker-compose -f docker-compose.test.yml up --build --abort-on-container-exit
        docker-compose -f docker-compose.test.yml down

  build:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main' || github.ref == 'refs/heads/staging'
    
    strategy:
      matrix:
        service: [content-manager, ai-processor, web-scraper, distributor, subscriber-manager, admin-dashboard]
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v2
    
    - name: Log in to Container Registry
      uses: docker/login-action@v2
      with:
        registry: ${{ env.REGISTRY }}
        username: ${{ github.actor }}
        password: ${{ secrets.GITHUB_TOKEN }}
    
    - name: Extract metadata
      id: meta
      uses: docker/metadata-action@v4
      with:
        images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}/${{ matrix.service }}
        tags: |
          type=ref,event=branch
          type=ref,event=pr
          type=sha,prefix={{branch}}-
    
    - name: Build and push Docker image
      uses: docker/build-push-action@v4
      with:
        context: ./services/${{ matrix.service }}
        file: ./services/${{ matrix.service }}/Dockerfile
        target: production
        push: true
        tags: ${{ steps.meta.outputs.tags }}
        labels: ${{ steps.meta.outputs.labels }}
        cache-from: type=gha
        cache-to: type=gha,mode=max

  deploy-staging:
    needs: build
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/staging'
    environment: staging
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Deploy to Staging
      run: |
        echo "Deploying to staging environment"
        # SSH to staging server and update services
        ssh ${{ secrets.STAGING_HOST }} << 'EOF'
          cd /opt/aquascene-content-engine
          git pull origin staging
          docker-compose -f docker-compose.staging.yml pull
          docker-compose -f docker-compose.staging.yml up -d --remove-orphans
        EOF
      env:
        DOCKER_HOST: ${{ secrets.STAGING_DOCKER_HOST }}

  deploy-production:
    needs: build
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    environment: production
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Configure kubectl
      uses: azure/k8s-set-context@v1
      with:
        method: kubeconfig
        kubeconfig: ${{ secrets.KUBE_CONFIG }}
    
    - name: Deploy to Kubernetes
      run: |
        # Update image tags in Kubernetes manifests
        sed -i "s|image: aquascene/content-manager:.*|image: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}/content-manager:main-${{ github.sha }}|g" kubernetes/content-manager-deployment.yaml
        
        # Apply Kubernetes manifests
        kubectl apply -f kubernetes/
        
        # Wait for rollout to complete
        kubectl rollout status deployment/content-manager -n aquascene-content-engine
        kubectl rollout status deployment/ai-processor -n aquascene-content-engine
        kubectl rollout status deployment/web-scraper -n aquascene-content-engine
        kubectl rollout status deployment/distributor -n aquascene-content-engine
        kubectl rollout status deployment/subscriber-manager -n aquascene-content-engine
    
    - name: Run smoke tests
      run: |
        kubectl run smoke-test --image=aquascene/smoke-tests:latest --rm -i --restart=Never \
          --env="BASE_URL=https://api.aquascene.com" \
          --env="API_KEY=${{ secrets.API_KEY }}" \
          -- /app/smoke-tests.sh

  notify:
    needs: [deploy-staging, deploy-production]
    runs-on: ubuntu-latest
    if: always()
    
    steps:
    - name: Notify Slack
      uses: 8398a7/action-slack@v3
      with:
        status: ${{ job.status }}
        webhook_url: ${{ secrets.SLACK_WEBHOOK }}
      if: always()
```

### Deployment Scripts
```bash
#!/bin/bash
# scripts/deploy.sh - Deployment automation script

set -e

ENVIRONMENT=${1:-development}
VERSION=${2:-latest}

echo "Deploying AquaScene Content Engine to $ENVIRONMENT (version: $VERSION)"

case $ENVIRONMENT in
  development)
    echo "Starting development environment..."
    docker-compose down
    docker-compose build
    docker-compose up -d
    docker-compose logs -f
    ;;
    
  staging)
    echo "Deploying to staging environment..."
    
    # Pull latest images
    docker-compose -f docker-compose.staging.yml pull
    
    # Health check before deployment
    if ! curl -f http://staging.aquascene.com/health; then
      echo "Staging environment unhealthy, aborting deployment"
      exit 1
    fi
    
    # Rolling update
    docker-compose -f docker-compose.staging.yml up -d --remove-orphans
    
    # Wait for services to be healthy
    ./scripts/wait-for-health.sh staging
    
    # Run smoke tests
    ./scripts/smoke-tests.sh staging
    ;;
    
  production)
    echo "Deploying to production environment..."
    
    # Blue-Green deployment
    ./scripts/blue-green-deploy.sh $VERSION
    
    # Run comprehensive health checks
    ./scripts/health-check.sh production
    
    # Run full test suite
    ./scripts/production-tests.sh
    ;;
    
  *)
    echo "Unknown environment: $ENVIRONMENT"
    exit 1
    ;;
esac

echo "Deployment completed successfully!"
```

### Blue-Green Deployment Script
```bash
#!/bin/bash
# scripts/blue-green-deploy.sh - Blue-Green deployment for production

set -e

VERSION=$1
NAMESPACE="aquascene-content-engine"

if [ -z "$VERSION" ]; then
  echo "Usage: $0 <version>"
  exit 1
fi

echo "Starting Blue-Green deployment for version $VERSION"

# Determine current and next colors
CURRENT_COLOR=$(kubectl get service content-manager -n $NAMESPACE -o jsonpath='{.spec.selector.color}')
if [ "$CURRENT_COLOR" = "blue" ]; then
  NEXT_COLOR="green"
else
  NEXT_COLOR="blue"
fi

echo "Current color: $CURRENT_COLOR, Next color: $NEXT_COLOR"

# Deploy new version to next color
echo "Deploying version $VERSION to $NEXT_COLOR environment"
sed -i "s/color: .*/color: $NEXT_COLOR/g" kubernetes/*-deployment.yaml
sed -i "s/image: .*/image: aquascene\/content-manager:$VERSION/g" kubernetes/*-deployment.yaml

kubectl apply -f kubernetes/ -n $NAMESPACE

# Wait for new deployment to be ready
echo "Waiting for $NEXT_COLOR deployment to be ready..."
kubectl rollout status deployment/content-manager-$NEXT_COLOR -n $NAMESPACE

# Run health checks on new deployment
echo "Running health checks on $NEXT_COLOR environment..."
kubectl run health-check --image=curlimages/curl --rm -i --restart=Never -n $NAMESPACE \
  -- curl -f http://content-manager-$NEXT_COLOR:8000/health

if [ $? -eq 0 ]; then
  echo "Health checks passed, switching traffic to $NEXT_COLOR"
  
  # Switch service to point to new deployment
  kubectl patch service content-manager -n $NAMESPACE -p '{"spec":{"selector":{"color":"'$NEXT_COLOR'"}}}'
  
  # Wait for a bit to ensure everything is working
  sleep 30
  
  # Run smoke tests
  echo "Running smoke tests on live traffic..."
  ./scripts/smoke-tests.sh production
  
  if [ $? -eq 0 ]; then
    echo "Smoke tests passed, cleaning up old $CURRENT_COLOR deployment"
    kubectl delete deployment content-manager-$CURRENT_COLOR -n $NAMESPACE
    echo "Blue-Green deployment completed successfully!"
  else
    echo "Smoke tests failed, rolling back..."
    kubectl patch service content-manager -n $NAMESPACE -p '{"spec":{"selector":{"color":"'$CURRENT_COLOR'"}}}'
    exit 1
  fi
else
  echo "Health checks failed, cleaning up failed deployment"
  kubectl delete deployment content-manager-$NEXT_COLOR -n $NAMESPACE
  exit 1
fi
```

## Configuration Management

### Environment-Specific Configuration
```yaml
# Configuration hierarchy
base_config.yaml              # Base configuration
├── development.yaml           # Development overrides
├── staging.yaml              # Staging overrides
└── production.yaml           # Production overrides

# Example: base_config.yaml
database:
  pool_size: 10
  max_overflow: 20
  pool_timeout: 30
  pool_recycle: 3600

redis:
  pool_size: 10
  timeout: 5

services:
  ai_processor:
    timeout: 300
    max_concurrent: 5
  web_scraper:
    rate_limit: 2
    timeout: 60

# Example: production.yaml (overrides)
database:
  pool_size: 25
  max_overflow: 50
  ssl_mode: require

redis:
  pool_size: 20
  cluster_mode: true
  sentinel_hosts:
    - redis-sentinel-1:26379
    - redis-sentinel-2:26379
    - redis-sentinel-3:26379

logging:
  level: WARN
  format: json
  handlers:
    - console
    - file
    - logstash

monitoring:
  enabled: true
  prometheus_endpoint: /metrics
  health_check_endpoint: /health
  metrics_port: 9090
```

### Secret Management
```yaml
# Kubernetes Secrets
apiVersion: v1
kind: Secret
metadata:
  name: database-secrets
  namespace: aquascene-content-engine
type: Opaque
data:
  url: cG9zdGdyZXNxbDovL3VzZXI6cGFzc3dvcmRAaG9zdDo1NDMyL2RhdGFiYXNl # base64 encoded
  password: cGFzc3dvcmQ= # base64 encoded

---
apiVersion: v1
kind: Secret
metadata:
  name: api-keys
  namespace: aquascene-content-engine
type: Opaque
data:
  openai_api_key: c2stYWJjZGVmZ2hpams= # base64 encoded
  anthropic_api_key: YW50aC1hYmNkZWZnaGlqaw== # base64 encoded
  sendgrid_api_key: U0cuYWJjZGVmZ2hpams= # base64 encoded
  jwt_secret: bXlfc2VjcmV0X2tleQ== # base64 encoded

---
# ConfigMap for non-sensitive configuration
apiVersion: v1
kind: ConfigMap
metadata:
  name: content-manager-config
  namespace: aquascene-content-engine
data:
  app_config.yaml: |
    environment: production
    debug: false
    log_level: INFO
    
    database:
      pool_size: 25
      pool_timeout: 30
      
    redis:
      pool_size: 20
      timeout: 5
      
    rate_limiting:
      requests_per_hour: 1000
      burst_size: 50
```

### Configuration Validation
```python
# Configuration validation and loading
from pydantic import BaseSettings, Field, validator
from typing import List, Optional
import yaml
import os

class DatabaseConfig(BaseSettings):
    url: str = Field(..., env='DATABASE_URL')
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30
    ssl_mode: str = 'prefer'
    
    @validator('pool_size')
    def validate_pool_size(cls, v):
        if v < 1 or v > 100:
            raise ValueError('Pool size must be between 1 and 100')
        return v

class RedisConfig(BaseSettings):
    url: str = Field(..., env='REDIS_URL')
    pool_size: int = 10
    timeout: int = 5
    cluster_mode: bool = False
    sentinel_hosts: Optional[List[str]] = None

class APIKeysConfig(BaseSettings):
    openai_api_key: Optional[str] = Field(None, env='OPENAI_API_KEY')
    anthropic_api_key: Optional[str] = Field(None, env='ANTHROPIC_API_KEY')
    sendgrid_api_key: Optional[str] = Field(None, env='SENDGRID_API_KEY')
    jwt_secret: str = Field(..., env='JWT_SECRET')
    
    @validator('jwt_secret')
    def validate_jwt_secret(cls, v):
        if len(v) < 32:
            raise ValueError('JWT secret must be at least 32 characters long')
        return v

class Config(BaseSettings):
    environment: str = Field('development', env='ENVIRONMENT')
    debug: bool = Field(False, env='DEBUG')
    log_level: str = Field('INFO', env='LOG_LEVEL')
    
    database: DatabaseConfig = DatabaseConfig()
    redis: RedisConfig = RedisConfig()
    api_keys: APIKeysConfig = APIKeysConfig()
    
    class Config:
        env_file = '.env'
        env_nested_delimiter = '__'

def load_config() -> Config:
    """Load configuration with validation"""
    
    # Load base configuration
    config_file = os.getenv('CONFIG_FILE', 'config/base_config.yaml')
    with open(config_file, 'r') as f:
        base_config = yaml.safe_load(f)
    
    # Load environment-specific overrides
    env = os.getenv('ENVIRONMENT', 'development')
    env_config_file = f'config/{env}.yaml'
    if os.path.exists(env_config_file):
        with open(env_config_file, 'r') as f:
            env_config = yaml.safe_load(f)
            # Deep merge configurations
            base_config.update(env_config)
    
    # Create and validate configuration
    config = Config(**base_config)
    
    return config
```

## Service Deployment Patterns

### Rolling Deployment
```yaml
# Kubernetes Rolling Update Strategy
spec:
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 25%        # Allow 25% more pods during update
      maxUnavailable: 25%  # Allow 25% of pods to be unavailable
  
  template:
    spec:
      containers:
      - name: content-manager
        image: aquascene/content-manager:v1.2.0
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
          failureThreshold: 3
```

### Canary Deployment
```yaml
# Canary deployment using Argo Rollouts
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: content-manager-rollout
spec:
  replicas: 10
  strategy:
    canary:
      steps:
      - setWeight: 10    # Route 10% of traffic to new version
      - pause: {duration: 5m}
      - setWeight: 25    # Route 25% of traffic to new version
      - pause: {duration: 10m}
      - setWeight: 50    # Route 50% of traffic to new version
      - pause: {duration: 10m}
      - setWeight: 100   # Route 100% of traffic to new version
      
      analysis:
        templates:
        - templateName: error-rate
        args:
        - name: service-name
          value: content-manager
          
  selector:
    matchLabels:
      app: content-manager
  template:
    metadata:
      labels:
        app: content-manager
    spec:
      containers:
      - name: content-manager
        image: aquascene/content-manager:v1.2.0
```

### Database Migration Strategy
```python
# Database migration deployment pattern
class MigrationManager:
    def __init__(self, db_connection, migration_dir: str):
        self.db = db_connection
        self.migration_dir = migration_dir
    
    async def run_migrations(self, target_version: Optional[str] = None):
        """Run database migrations with rollback capability"""
        
        # Get current database version
        current_version = await self.get_current_version()
        
        # Get available migrations
        migrations = self.get_pending_migrations(current_version, target_version)
        
        if not migrations:
            logger.info("No pending migrations")
            return
        
        # Create migration transaction
        async with self.db.transaction():
            try:
                for migration in migrations:
                    logger.info(f"Running migration: {migration.name}")
                    
                    # Run migration
                    await self.execute_migration(migration)
                    
                    # Update version table
                    await self.update_version(migration.version)
                    
                    logger.info(f"Migration {migration.name} completed")
                
                logger.info("All migrations completed successfully")
                
            except Exception as e:
                logger.error(f"Migration failed: {e}")
                # Transaction will automatically rollback
                raise

# Migration execution in deployment
async def deploy_with_migrations():
    """Deploy application with database migrations"""
    
    # 1. Run database migrations
    migration_manager = MigrationManager(db_connection, "migrations/")
    await migration_manager.run_migrations()
    
    # 2. Deploy application services
    await deploy_services()
    
    # 3. Run post-deployment validations
    await validate_deployment()
```

## Database Deployment

### PostgreSQL High Availability Setup
```yaml
# PostgreSQL cluster configuration using PostgreSQL Operator
apiVersion: postgresql.cnpg.io/v1
kind: Cluster
metadata:
  name: postgres-cluster
  namespace: aquascene-content-engine
spec:
  instances: 3
  
  postgresql:
    parameters:
      max_connections: "200"
      shared_buffers: "256MB"
      effective_cache_size: "1GB"
      maintenance_work_mem: "64MB"
      checkpoint_completion_target: "0.9"
      wal_buffers: "16MB"
      default_statistics_target: "100"
      random_page_cost: "1.1"
      effective_io_concurrency: "200"
      work_mem: "4MB"
      min_wal_size: "1GB"
      max_wal_size: "4GB"
  
  bootstrap:
    initdb:
      database: content_engine
      owner: postgres
      secret:
        name: postgres-credentials
  
  storage:
    size: 100Gi
    storageClass: fast-ssd
  
  monitoring:
    enabled: true
    
  backup:
    barmanObjectStore:
      destinationPath: "s3://aquascene-backups/postgres"
      s3Credentials:
        accessKeyId:
          name: backup-credentials
          key: ACCESS_KEY_ID
        secretAccessKey:
          name: backup-credentials
          key: SECRET_ACCESS_KEY
      wal:
        retention: "7d"
      data:
        retention: "30d"
        
  resources:
    requests:
      memory: "1Gi"
      cpu: "500m"
    limits:
      memory: "2Gi"
      cpu: "1000m"
```

### Redis Cluster Deployment
```yaml
# Redis Cluster using Redis Operator
apiVersion: redis.redis.opstreelabs.in/v1beta1
kind: RedisCluster
metadata:
  name: redis-cluster
  namespace: aquascene-content-engine
spec:
  clusterSize: 6
  clusterVersion: v7
  persistenceEnabled: true
  redisExporter:
    enabled: true
    image: oliver006/redis_exporter:latest
  
  storage:
    volumeClaimTemplate:
      spec:
        accessModes: ["ReadWriteOnce"]
        resources:
          requests:
            storage: 10Gi
        storageClassName: fast-ssd
  
  resources:
    requests:
      memory: 512Mi
      cpu: 250m
    limits:
      memory: 1Gi
      cpu: 500m
      
  securityContext:
    runAsUser: 1000
    fsGroup: 1000
    
  redisConfig:
    save: "900 1"
    maxmemory-policy: "allkeys-lru"
    timeout: "300"
    tcp-keepalive: "300"
```

## High Availability Deployment

### Multi-Zone Deployment
```yaml
# Node affinity for multi-zone deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: content-manager
spec:
  replicas: 6  # 2 replicas per zone across 3 zones
  template:
    spec:
      affinity:
        podAntiAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
          - weight: 100
            podAffinityTerm:
              labelSelector:
                matchExpressions:
                - key: app
                  operator: In
                  values:
                  - content-manager
              topologyKey: kubernetes.io/hostname
          - weight: 50
            podAffinityTerm:
              labelSelector:
                matchExpressions:
                - key: app
                  operator: In
                  values:
                  - content-manager
              topologyKey: failure-domain.beta.kubernetes.io/zone
      
      nodeAffinity:
        preferredDuringSchedulingIgnoredDuringExecution:
        - weight: 1
          preference:
            matchExpressions:
            - key: failure-domain.beta.kubernetes.io/zone
              operator: In
              values:
              - us-west1-a
              - us-west1-b
              - us-west1-c
```

### Load Balancer Configuration
```yaml
# Ingress with multiple backends and health checks
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: content-engine-ingress
  annotations:
    kubernetes.io/ingress.class: nginx
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/use-regex: "true"
    nginx.ingress.kubernetes.io/rate-limit: "100"
    nginx.ingress.kubernetes.io/upstream-hash-by: "$remote_addr"
    nginx.ingress.kubernetes.io/load-balance: "round_robin"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  tls:
  - hosts:
    - api.aquascene.com
    secretName: aquascene-tls
  rules:
  - host: api.aquascene.com
    http:
      paths:
      - path: /api/v1/content
        pathType: Prefix
        backend:
          service:
            name: content-manager
            port:
              number: 8000
      - path: /api/v1/generate
        pathType: Prefix
        backend:
          service:
            name: ai-processor
            port:
              number: 8001
      - path: /api/v1/subscribers
        pathType: Prefix
        backend:
          service:
            name: subscriber-manager
            port:
              number: 8004
```

This comprehensive deployment architecture documentation provides the technical foundation for deploying the AquaScene Content Engine across different environments with proper automation, configuration management, and high availability patterns.