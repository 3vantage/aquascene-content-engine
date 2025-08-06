# AquaScene Content Engine - Troubleshooting Guide

**Version:** 1.0  
**Last Updated:** August 6, 2025  
**Status:** Production Ready

## Overview

This comprehensive troubleshooting guide provides solutions for common issues encountered when working with the AquaScene Content Engine. Issues are categorized by component and severity level for quick resolution.

## Table of Contents

1. [Quick Diagnostics](#quick-diagnostics)
2. [Service-Specific Issues](#service-specific-issues)
3. [Infrastructure Issues](#infrastructure-issues)
4. [Performance Issues](#performance-issues)
5. [Security and Authentication](#security-and-authentication)
6. [AI and Content Generation](#ai-and-content-generation)
7. [Monitoring and Logging](#monitoring-and-logging)
8. [Common Error Messages](#common-error-messages)
9. [Emergency Procedures](#emergency-procedures)
10. [Preventive Measures](#preventive-measures)

## Quick Diagnostics

### System Health Check Script

```bash
#!/bin/bash
# quick-diagnosis.sh - Run this first for immediate system overview

echo "🔍 AquaScene Content Engine - Quick Diagnosis"
echo "=============================================="

# Check Docker status
echo "📋 Docker Status:"
if docker info >/dev/null 2>&1; then
    echo "✅ Docker is running"
    docker --version
else
    echo "❌ Docker is not running or accessible"
    exit 1
fi

# Check available resources
echo -e "\n💾 System Resources:"
echo "Memory: $(free -h | awk '/^Mem:/ {print $3 "/" $2}')"
echo "Disk: $(df -h / | awk 'NR==2 {print $3 "/" $2 " (" $5 " used)"}')"
echo "CPU Load: $(uptime | awk -F'load average:' '{print $2}')"

# Check container status
echo -e "\n🐳 Container Status:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | head -20

# Check critical ports
echo -e "\n🔌 Port Status:"
critical_ports=(5432 6379 8000 8001 3000 9090)
for port in "${critical_ports[@]}"; do
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo "✅ Port $port is in use"
    else
        echo "❌ Port $port is not in use"
    fi
done

# Quick service health check
echo -e "\n🏥 Service Health:"
services=("http://localhost:8000/health" "http://localhost:8001/health")
for service in "${services[@]}"; do
    if curl -f -s "$service" >/dev/null 2>&1; then
        echo "✅ $service is healthy"
    else
        echo "❌ $service is unhealthy or unreachable"
    fi
done

# Check recent errors in logs
echo -e "\n📝 Recent Errors (last 50 lines):"
docker-compose logs --tail=50 | grep -i error | tail -5 || echo "No recent errors found"

echo -e "\n🔧 Run './run-full-test-suite.sh' for comprehensive testing"
```

### Quick Fix Commands

```bash
# Restart all services
docker-compose restart

# Clean restart (removes containers and recreates)
docker-compose down && docker-compose up -d

# Fix permission issues
sudo chown -R $USER:$USER .
chmod +x *.sh

# Clean Docker resources
docker system prune -f

# Reset and rebuild everything
docker-compose down -v
docker system prune -af
./fix-dependencies.sh
./start-services.sh
```

## Service-Specific Issues

### AI Processor Service (Port 8001)

#### Issue: Service fails to start

**Symptoms:**
- Container exits immediately
- Port 8001 not responding
- Error logs show import errors

**Diagnosis:**
```bash
# Check container status
docker ps -a | grep ai-processor

# View detailed logs
docker logs ai-processor --tail=50

# Check if port is blocked
lsof -i :8001
```

**Common Causes & Solutions:**

1. **API Key Issues**
   ```bash
   # Verify API keys are set
   docker exec ai-processor env | grep -E "(OPENAI|ANTHROPIC)_API_KEY"
   
   # Test API key validity
   curl -H "Authorization: Bearer $OPENAI_API_KEY" \
        https://api.openai.com/v1/models | jq '.data[0]'
   ```

2. **Dependency Conflicts**
   ```bash
   # Rebuild with latest dependencies
   cd services/ai-processor
   docker build --no-cache -t ai-processor .
   docker-compose up -d ai-processor
   ```

3. **Memory Issues**
   ```bash
   # Check memory usage
   docker stats ai-processor --no-stream
   
   # Increase memory limit in docker-compose.yml
   mem_limit: 2g
   memswap_limit: 2g
   ```

#### Issue: Slow content generation

**Symptoms:**
- API timeouts
- Long response times (>30 seconds)
- High CPU usage

**Solutions:**
```bash
# Check current performance
curl -s http://localhost:8001/stats | jq '.'

# Reduce concurrent requests
docker exec ai-processor env | grep MAX_CONCURRENT
# Set MAX_CONCURRENT_REQUESTS=3 in .env

# Enable caching
# Set ENABLE_LLM_CACHING=true in .env

# Switch to faster model
# Set OPENAI_MODEL=gpt-3.5-turbo in .env
```

#### Issue: Content quality issues

**Symptoms:**
- Low quality scores
- Validation failures
- Inconsistent brand voice

**Solutions:**
```bash
# Check knowledge base status
docker exec ai-processor curl -s http://localhost:8001/debug/knowledge-base

# Update knowledge base
docker exec ai-processor python -c "
from src.knowledge.aquascaping_kb import AquascapingKB
kb = AquascapingKB()
print(f'Plants: {len(kb.plants)}')
print(f'Equipment: {len(kb.equipment)}')
"

# Adjust quality thresholds
# Edit services/ai-processor/src/validators/quality_validator.py
# Lower minimum_score if needed for development
```

### Content Manager Service (Port 8000)

#### Issue: Database connection errors

**Symptoms:**
- "Could not connect to database" errors
- Service health check fails
- API returns 500 errors

**Diagnosis:**
```bash
# Test database connection
docker exec postgres pg_isready -U postgres -d content_engine

# Check connection string
docker exec content-manager env | grep DATABASE_URL

# Test from content manager
docker exec content-manager python -c "
import asyncpg
import asyncio
async def test():
    try:
        conn = await asyncpg.connect('$DATABASE_URL')
        await conn.close()
        print('✅ Database connection successful')
    except Exception as e:
        print(f'❌ Database connection failed: {e}')
asyncio.run(test())
"
```

**Solutions:**
```bash
# Restart PostgreSQL
docker-compose restart postgres

# Wait for database to be ready
docker-compose exec postgres sh -c '
    until pg_isready -U postgres; do
        echo "Waiting for postgres..."
        sleep 2
    done
'

# Recreate database connection
docker-compose restart content-manager
```

#### Issue: API endpoints returning 404

**Symptoms:**
- Specific endpoints not found
- Nginx proxy errors
- Route registration issues

**Solutions:**
```bash
# Check registered routes
docker exec content-manager python -c "
from src.main import app
for route in app.routes:
    print(f'{route.path} - {route.methods}')
"

# Test direct connection (bypass proxy)
curl http://localhost:8000/api/v1/content

# Check Nginx configuration
docker exec nginx nginx -t
docker-compose restart nginx
```

### PostgreSQL Database Issues

#### Issue: Database won't start

**Symptoms:**
- Container exits with error
- pg_isready fails
- Data directory errors

**Diagnosis:**
```bash
# Check PostgreSQL logs
docker logs postgres

# Check data directory permissions
docker run --rm -v postgres_data:/data alpine ls -la /data

# Check available disk space
df -h
```

**Solutions:**

1. **Permission Issues**
   ```bash
   # Fix data directory permissions
   docker run --rm -v postgres_data:/data alpine chown -R 999:999 /data
   docker-compose restart postgres
   ```

2. **Corrupted Data**
   ```bash
   # Stop all services
   docker-compose down
   
   # Remove corrupted volume
   docker volume rm content_engine_postgres_data
   
   # Recreate from backup
   docker volume create postgres_data
   ./scripts/restore-database.sh /path/to/backup.sql.gz
   ```

3. **Port Conflict**
   ```bash
   # Check what's using port 5432
   lsof -i :5432
   
   # Kill conflicting process or change port
   sudo systemctl stop postgresql
   ```

#### Issue: Database performance problems

**Symptoms:**
- Slow query responses
- High CPU usage
- Connection timeouts

**Solutions:**
```bash
# Check active connections
docker exec postgres psql -U postgres -c "
    SELECT count(*) as active_connections 
    FROM pg_stat_activity 
    WHERE state = 'active';"

# Analyze slow queries
docker exec postgres psql -U postgres -c "
    SELECT query, mean_time, calls 
    FROM pg_stat_statements 
    ORDER BY mean_time DESC 
    LIMIT 10;"

# Optimize database settings
docker exec postgres psql -U postgres -c "
    ALTER SYSTEM SET shared_buffers = '256MB';
    ALTER SYSTEM SET effective_cache_size = '1GB';
    ALTER SYSTEM SET work_mem = '64MB';
    SELECT pg_reload_conf();"
```

### Redis Cache Issues

#### Issue: Redis connection failures

**Symptoms:**
- "Connection refused" errors
- Cache misses
- Session data lost

**Diagnosis:**
```bash
# Test Redis connection
docker exec redis redis-cli ping

# Check Redis authentication
docker exec redis redis-cli -a $REDIS_PASSWORD ping

# View Redis logs
docker logs redis --tail=50
```

**Solutions:**
```bash
# Restart Redis
docker-compose restart redis

# Clear Redis data (if corrupted)
docker exec redis redis-cli -a $REDIS_PASSWORD flushall

# Test from application
docker exec content-manager python -c "
import redis
r = redis.Redis(host='redis', port=6379, password='$REDIS_PASSWORD')
r.set('test', 'value')
print(r.get('test'))
"
```

#### Issue: High memory usage

**Symptoms:**
- Redis OOM errors
- Slow cache operations
- Memory warnings

**Solutions:**
```bash
# Check Redis memory usage
docker exec redis redis-cli -a $REDIS_PASSWORD info memory

# Set memory limit
docker exec redis redis-cli -a $REDIS_PASSWORD config set maxmemory 512mb
docker exec redis redis-cli -a $REDIS_PASSWORD config set maxmemory-policy allkeys-lru

# Clean expired keys
docker exec redis redis-cli -a $REDIS_PASSWORD eval "
    for i=1,redis.call('dbsize') do
        local keys = redis.call('scan', 0, 'count', 1000)
        for j=1,#keys[2] do
            if redis.call('ttl', keys[2][j]) == -1 then
                redis.call('expire', keys[2][j], 86400)
            end
        end
    end
" 0
```

## Infrastructure Issues

### Docker and Container Issues

#### Issue: Container keeps restarting

**Symptoms:**
- Container status shows "Restarting"
- Frequent exit codes 1 or 125
- Service intermittently unavailable

**Diagnosis:**
```bash
# Check container restart count
docker ps -a --format "table {{.Names}}\t{{.Status}}\t{{.Command}}"

# View container events
docker events --filter container=ai-processor --since="1h"

# Check resource limits
docker stats --no-stream
```

**Solutions:**

1. **Memory Limits**
   ```bash
   # Increase memory limit
   # In docker-compose.yml:
   mem_limit: 2g
   memswap_limit: 2g
   
   # Or remove limits temporarily
   # Comment out mem_limit and memswap_limit
   ```

2. **Health Check Issues**
   ```bash
   # Disable health check temporarily
   # In docker-compose.yml:
   healthcheck:
     disable: true
   
   # Or increase timeout
   healthcheck:
     test: ["CMD-SHELL", "curl -f http://localhost:8001/health || exit 1"]
     interval: 60s
     timeout: 30s
     retries: 5
     start_period: 120s
   ```

3. **Application Errors**
   ```bash
   # Check application logs
   docker logs container-name --tail=100
   
   # Run container interactively for debugging
   docker run -it --rm \
     -e DATABASE_URL=$DATABASE_URL \
     -e REDIS_URL=$REDIS_URL \
     ai-processor bash
   ```

#### Issue: Network connectivity problems

**Symptoms:**
- Services can't reach each other
- DNS resolution failures
- Timeout errors between containers

**Diagnosis:**
```bash
# Check networks
docker network ls
docker network inspect content-engine_content-engine

# Test connectivity between containers
docker exec content-manager ping ai-processor
docker exec ai-processor nslookup postgres

# Check iptables rules
sudo iptables -L DOCKER-USER
```

**Solutions:**
```bash
# Recreate network
docker-compose down
docker network prune
docker-compose up -d

# Reset Docker networking
sudo systemctl restart docker

# Check for port conflicts
netstat -tlpn | grep -E "(5432|6379|8000|8001)"
```

### Disk Space Issues

#### Issue: Insufficient disk space

**Symptoms:**
- "No space left on device" errors
- Container startup failures
- Database write errors

**Immediate Actions:**
```bash
# Check disk usage
df -h
du -sh /var/lib/docker

# Emergency cleanup
docker system prune -af --volumes
docker volume prune

# Remove old logs
find /var/log -name "*.log" -mtime +7 -delete
```

**Long-term Solutions:**
```bash
# Set up log rotation
sudo tee /etc/logrotate.d/docker-containers << EOF
/var/lib/docker/containers/*/*-json.log {
    daily
    rotate 7
    compress
    size 1M
    missingok
    delaycompress
    copytruncate
}
EOF

# Configure Docker daemon
sudo tee /etc/docker/daemon.json << EOF
{
    "log-driver": "json-file",
    "log-opts": {
        "max-size": "100m",
        "max-file": "3"
    }
}
EOF
sudo systemctl restart docker
```

## Performance Issues

### High CPU Usage

#### Diagnosis
```bash
# Check overall system load
top -bn1 | head -10

# Check container CPU usage
docker stats --no-stream

# Identify CPU-intensive processes
docker exec ai-processor ps aux --sort=-%cpu | head -10
```

#### Solutions

1. **Reduce Concurrent Processing**
   ```bash
   # Lower concurrent requests in AI processor
   # In .env:
   MAX_CONCURRENT_REQUESTS=3
   
   # Restart service
   docker-compose restart ai-processor
   ```

2. **Optimize Database Queries**
   ```bash
   # Enable query logging
   docker exec postgres psql -U postgres -c "
       ALTER SYSTEM SET log_statement = 'all';
       ALTER SYSTEM SET log_min_duration_statement = 1000;
       SELECT pg_reload_conf();"
   
   # Check slow queries
   docker exec postgres tail -f /var/lib/postgresql/data/log/postgresql*.log
   ```

3. **Scale Services Horizontally**
   ```yaml
   # In docker-compose.yml
   ai-processor:
     deploy:
       replicas: 3
   
   # Or use Docker Swarm
   docker service scale aquascene_ai-processor=3
   ```

### High Memory Usage

#### Diagnosis
```bash
# Check memory usage by container
docker stats --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}"

# Check system memory
free -h
cat /proc/meminfo

# Check for memory leaks
docker exec ai-processor ps aux --sort=-%mem
```

#### Solutions

1. **Increase Container Memory Limits**
   ```yaml
   # In docker-compose.yml
   services:
     ai-processor:
       mem_limit: 4g
       memswap_limit: 4g
   ```

2. **Enable Memory Monitoring**
   ```bash
   # Add to Prometheus monitoring
   # Check memory usage trends
   curl -s 'http://localhost:9090/api/v1/query?query=container_memory_usage_bytes' | jq .
   ```

3. **Optimize Application Memory Usage**
   ```python
   # In Python services, add memory profiling
   import psutil
   import gc
   
   def log_memory_usage():
       process = psutil.Process()
       memory_mb = process.memory_info().rss / 1024 / 1024
       print(f"Memory usage: {memory_mb:.2f} MB")
   
   # Force garbage collection
   gc.collect()
   ```

### Slow Response Times

#### Diagnosis
```bash
# Test API response times
time curl -s http://localhost:8001/health

# Check database query performance
docker exec postgres psql -U postgres -c "
    SELECT query, mean_time, calls, total_time
    FROM pg_stat_statements 
    ORDER BY mean_time DESC 
    LIMIT 10;"

# Monitor with continuous testing
while true; do
    curl -w "Time: %{time_total}s\n" -s -o /dev/null http://localhost:8001/generate \
         -H "Content-Type: application/json" \
         -d '{"content_type":"newsletter_article","topic":"test"}'
    sleep 5
done
```

#### Solutions

1. **Enable Caching**
   ```bash
   # In .env
   ENABLE_LLM_CACHING=true
   REDIS_CACHE_TTL=3600
   
   # Restart services
   docker-compose restart ai-processor content-manager
   ```

2. **Database Optimization**
   ```bash
   # Add indexes
   docker exec postgres psql -U postgres -d content_engine -c "
       CREATE INDEX CONCURRENTLY idx_content_created_at 
       ON content_pieces (created_at DESC);
       
       CREATE INDEX CONCURRENTLY idx_content_type_status 
       ON content_pieces (content_type, status);"
   ```

3. **Load Balancing**
   ```yaml
   # Add HAProxy for load balancing
   haproxy:
     image: haproxy:latest
     volumes:
       - ./infrastructure/haproxy/haproxy.cfg:/usr/local/etc/haproxy/haproxy.cfg
     ports:
       - "80:80"
   ```

## Security and Authentication

### Authentication Failures

#### Issue: JWT token errors

**Symptoms:**
- "Invalid token" errors
- 401 Unauthorized responses
- Token expiration issues

**Diagnosis:**
```bash
# Check JWT secret
docker exec content-manager env | grep JWT_SECRET

# Validate token format
echo "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." | base64 -d

# Check token expiration
docker exec content-manager python -c "
import jwt
import os
token = 'your-token-here'
try:
    decoded = jwt.decode(token, os.getenv('JWT_SECRET'), algorithms=['HS256'])
    print('Token is valid:', decoded)
except jwt.ExpiredSignatureError:
    print('Token has expired')
except jwt.InvalidTokenError as e:
    print('Invalid token:', e)
"
```

**Solutions:**
```bash
# Generate new JWT secret
openssl rand -base64 32

# Update JWT settings in .env
JWT_SECRET=your-new-secret-here
JWT_EXPIRATION_HOURS=24

# Restart services
docker-compose restart content-manager subscriber-manager
```

#### Issue: API key validation errors

**Symptoms:**
- External API calls failing
- "Invalid API key" errors
- Rate limiting issues

**Solutions:**
```bash
# Test OpenAI API key
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
     "https://api.openai.com/v1/models" | jq '.data[0].id'

# Test Anthropic API key
curl -H "x-api-key: $ANTHROPIC_API_KEY" \
     "https://api.anthropic.com/v1/messages" \
     -H "Content-Type: application/json" \
     -d '{"model":"claude-3-haiku-20240307","max_tokens":1024,"messages":[{"role":"user","content":"Hello"}]}'

# Rotate API keys if compromised
# Update .env with new keys
# Restart AI processor
docker-compose restart ai-processor
```

### SSL/TLS Issues

#### Issue: Certificate problems

**Symptoms:**
- "SSL certificate has expired" errors
- "Certificate not trusted" warnings
- HTTPS connection failures

**Solutions:**
```bash
# Check certificate expiration
openssl x509 -in /path/to/cert.pem -noout -dates

# Renew Let's Encrypt certificate
sudo certbot renew

# Test SSL configuration
curl -I https://your-domain.com
openssl s_client -connect your-domain.com:443 -servername your-domain.com

# Update Nginx configuration
docker exec nginx nginx -t
docker-compose restart nginx
```

## AI and Content Generation

### LLM Integration Issues

#### Issue: OpenAI API failures

**Symptoms:**
- "Rate limit exceeded" errors
- "Model not found" errors
- Timeout errors

**Diagnosis:**
```bash
# Check API key and quota
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
     "https://api.openai.com/v1/usage?date=$(date -d '1 month ago' '+%Y-%m-%d')" | jq .

# Test different models
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
     "https://api.openai.com/v1/models" | jq '.data[] | .id' | grep gpt
```

**Solutions:**
```bash
# Implement exponential backoff
# In services/ai-processor/src/llm_clients/openai_client.py
import time
import random

def retry_with_backoff(func, max_retries=3):
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            wait_time = (2 ** attempt) + random.uniform(0, 1)
            time.sleep(wait_time)

# Switch to alternative model
# In .env:
OPENAI_MODEL=gpt-3.5-turbo  # Instead of gpt-4

# Enable request logging
LOG_LEVEL=DEBUG
```

#### Issue: Content quality validation failing

**Symptoms:**
- Low quality scores consistently
- Validation errors
- Content rejected

**Solutions:**
```bash
# Check knowledge base status
docker exec ai-processor python -c "
from src.knowledge.aquascaping_kb import AquascapingKB
kb = AquascapingKB()
print('Knowledge base loaded successfully')
print(f'Plants: {len(kb.plants)}')
print(f'Equipment: {len(kb.equipment)}')
"

# Adjust validation thresholds
# Edit services/ai-processor/src/validators/quality_validator.py
# Reduce minimum acceptable scores for development

# Test validation manually
docker exec ai-processor python -c "
from src.validators.quality_validator import QualityValidator
validator = QualityValidator()
result = validator.validate('Your test content here', 'newsletter_article')
print(f'Quality score: {result.score}')
print(f'Issues: {result.issues}')
"
```

### Batch Processing Issues

#### Issue: Batch jobs failing

**Symptoms:**
- Partial batch completion
- Memory errors during large batches
- Timeout errors

**Solutions:**
```bash
# Reduce batch size
# In AI processor configuration:
MAX_CONCURRENT_REQUESTS=2
BATCH_SIZE_LIMIT=5

# Monitor batch progress
curl http://localhost:8001/batch/status/batch-id

# Implement batch checkpointing
# Save progress after each successful item
# Resume from last successful checkpoint
```

## Monitoring and Logging

### Prometheus Issues

#### Issue: Metrics not being collected

**Symptoms:**
- Empty Grafana dashboards
- Missing metrics in Prometheus
- Scrape errors

**Diagnosis:**
```bash
# Check Prometheus targets
curl -s http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | {job: .labels.job, health: .health, lastError: .lastError}'

# Test metrics endpoints directly
curl http://localhost:8001/metrics
curl http://localhost:8000/metrics
```

**Solutions:**
```bash
# Restart Prometheus
docker-compose restart prometheus

# Check Prometheus configuration
docker exec prometheus cat /etc/prometheus/prometheus.yml

# Verify service discovery
docker exec prometheus wget -qO- http://content-manager:8000/metrics
```

#### Issue: Grafana dashboard problems

**Symptoms:**
- "No data points" in panels
- Dashboard loading errors
- Authentication issues

**Solutions:**
```bash
# Reset Grafana admin password
docker exec grafana grafana-cli admin reset-admin-password newpassword

# Check data source connection
curl -s http://admin:admin@localhost:3000/api/datasources | jq .

# Import dashboards manually
# Copy dashboard JSON files to grafana/dashboards/
docker-compose restart grafana
```

### Logging Issues

#### Issue: Logs not appearing

**Symptoms:**
- Empty log files
- Missing application logs
- Log aggregation failures

**Solutions:**
```bash
# Check Docker logging driver
docker info | grep "Logging Driver"

# View container logs directly
docker logs ai-processor --tail=100

# Check log file permissions
ls -la logs/

# Reset logging configuration
docker-compose down
docker-compose up -d
```

## Common Error Messages

### Database Errors

#### "Connection to server at localhost:5432 refused"

**Cause:** PostgreSQL service not running or network issues

**Solution:**
```bash
# Check if PostgreSQL is running
docker ps | grep postgres

# Restart PostgreSQL
docker-compose restart postgres

# Check network connectivity
docker exec content-manager ping postgres
```

#### "FATAL: password authentication failed"

**Cause:** Incorrect database credentials

**Solution:**
```bash
# Verify database credentials
docker exec postgres psql -U postgres -d content_engine -c "SELECT 1;"

# Reset password if needed
docker exec postgres psql -U postgres -c "ALTER USER postgres PASSWORD 'newpassword';"

# Update .env file with correct credentials
```

### Redis Errors

#### "NOAUTH Authentication required"

**Cause:** Redis authentication not configured properly

**Solution:**
```bash
# Check Redis authentication
docker exec redis redis-cli -a $REDIS_PASSWORD ping

# Verify password in configuration
docker exec redis cat /usr/local/etc/redis/redis.conf | grep requirepass

# Update Redis URL with password
REDIS_URL=redis://:your-password@redis:6379
```

### API Errors

#### "504 Gateway Timeout"

**Cause:** Upstream service not responding

**Solution:**
```bash
# Check upstream service health
curl http://localhost:8001/health

# Check Nginx configuration
docker exec nginx nginx -t

# Increase timeout in nginx configuration
# proxy_read_timeout 300s;
# proxy_connect_timeout 300s;
```

#### "413 Request Entity Too Large"

**Cause:** Request payload too large for Nginx

**Solution:**
```bash
# Increase client_max_body_size in nginx.conf
client_max_body_size 100M;

# Restart Nginx
docker-compose restart nginx
```

### AI Service Errors

#### "Model not found"

**Cause:** Specified AI model not available

**Solution:**
```bash
# Check available models
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
     "https://api.openai.com/v1/models" | jq '.data[].id'

# Update model in configuration
OPENAI_MODEL=gpt-3.5-turbo
```

#### "Rate limit exceeded"

**Cause:** Too many API requests to AI provider

**Solution:**
```bash
# Implement rate limiting
RATE_LIMIT_REQUESTS_PER_MINUTE=10

# Add delays between requests
# Enable caching to reduce API calls
ENABLE_LLM_CACHING=true
```

## Emergency Procedures

### System Recovery

#### Complete System Failure

**Steps:**
1. **Assess the situation**
   ```bash
   # Check system status
   docker ps -a
   docker-compose logs --tail=50
   ```

2. **Stop all services**
   ```bash
   docker-compose down
   ```

3. **Check system resources**
   ```bash
   df -h  # Disk space
   free -h  # Memory
   top  # CPU usage
   ```

4. **Restore from backup**
   ```bash
   # Restore latest backup
   ./scripts/restore-full-backup.sh /backups/latest/
   ```

5. **Start core services only**
   ```bash
   docker-compose up -d postgres redis
   # Wait for services to be ready
   sleep 30
   ```

6. **Start application services**
   ```bash
   docker-compose up -d content-manager ai-processor
   ```

7. **Verify system health**
   ```bash
   ./run-full-test-suite.sh
   ```

#### Data Corruption Recovery

**Steps:**
1. **Stop all services immediately**
   ```bash
   docker-compose down
   ```

2. **Assess corruption extent**
   ```bash
   # Check PostgreSQL data integrity
   docker run --rm -v postgres_data:/data alpine ls -la /data
   
   # Check for corrupted files
   docker run --rm -v postgres_data:/data postgres:15 \
     pg_controldata /data
   ```

3. **Restore from latest backup**
   ```bash
   # Find latest backup
   ls -la /backups/ | grep -E "content_engine_backup.*\.sql\.gz"
   
   # Restore database
   ./scripts/restore-database.sh /backups/latest-backup.sql.gz
   ```

4. **Verify data integrity**
   ```bash
   # Check database consistency
   docker exec postgres psql -U postgres -d content_engine -c "
       SELECT schemaname, tablename, n_tup_ins, n_tup_del 
       FROM pg_stat_user_tables;"
   ```

### Security Incidents

#### Suspected Breach Response

**Immediate Actions:**
1. **Isolate the system**
   ```bash
   # Block external traffic
   sudo ufw deny out
   
   # Stop non-essential services
   docker-compose stop admin-dashboard nginx
   ```

2. **Change all credentials**
   ```bash
   # Generate new secrets
   openssl rand -base64 32 > jwt_secret.txt
   openssl rand -base64 32 > encryption_key.txt
   
   # Update database passwords
   docker exec postgres psql -U postgres -c "
       ALTER USER postgres PASSWORD 'new-secure-password';"
   ```

3. **Audit logs**
   ```bash
   # Check access logs
   grep -E "(admin|login|auth)" logs/*.log
   
   # Check for unusual activity
   docker-compose logs | grep -E "(error|failed|unauthorized)" | tail -100
   ```

4. **Backup current state**
   ```bash
   # Create forensic backup before cleanup
   ./scripts/full-backup.sh
   mv /backups/latest /backups/forensic-$(date +%Y%m%d-%H%M%S)
   ```

#### API Key Compromise

**Steps:**
1. **Immediately revoke compromised keys**
   ```bash
   # Remove from environment
   unset OPENAI_API_KEY
   unset ANTHROPIC_API_KEY
   
   # Update .env file
   sed -i 's/OPENAI_API_KEY=.*/OPENAI_API_KEY=/' .env
   ```

2. **Generate new API keys**
   - OpenAI: https://platform.openai.com/api-keys
   - Anthropic: https://console.anthropic.com/

3. **Update configuration**
   ```bash
   # Update .env with new keys
   nano .env
   
   # Restart AI services
   docker-compose restart ai-processor
   ```

4. **Monitor for unusual usage**
   ```bash
   # Check API usage patterns
   curl -H "Authorization: Bearer $NEW_OPENAI_API_KEY" \
        "https://api.openai.com/v1/usage" | jq .
   ```

## Preventive Measures

### Regular Maintenance

#### Daily Checks
```bash
#!/bin/bash
# daily-health-check.sh

# System health
./quick-diagnosis.sh

# Backup verification
ls -la /backups/ | tail -5

# Log cleanup
find logs/ -name "*.log" -size +100M -exec truncate -s 50M {} \;

# Security updates check
if command -v apt >/dev/null; then
    apt list --upgradable 2>/dev/null | grep -i security
fi
```

#### Weekly Maintenance
```bash
#!/bin/bash
# weekly-maintenance.sh

# Full system backup
./scripts/full-backup.sh

# Docker cleanup
docker system prune -f

# Certificate check
./scripts/check-certificates.sh

# Performance baseline
./scripts/performance-benchmark.sh
```

### Monitoring Setup

#### Alerting Rules
```yaml
# Add to prometheus/alert-rules.yml
- alert: ServiceDown
  expr: up == 0
  for: 1m
  labels:
    severity: critical
  annotations:
    summary: "Service {{ $labels.job }} is down"

- alert: HighErrorRate
  expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "High error rate detected"

- alert: DiskSpaceLow
  expr: (node_filesystem_avail_bytes / node_filesystem_size_bytes) * 100 < 10
  for: 5m
  labels:
    severity: critical
  annotations:
    summary: "Disk space critically low"
```

#### Health Monitoring
```bash
#!/bin/bash
# continuous-monitoring.sh

while true; do
    # Check service health
    if ! curl -f -s http://localhost:8001/health >/dev/null; then
        echo "$(date): AI Processor unhealthy" >> health-alerts.log
        # Send alert (email, Slack, etc.)
    fi
    
    # Check resource usage
    memory_usage=$(free | awk '/^Mem:/ {printf "%.0f", ($3/$2)*100}')
    if [ "$memory_usage" -gt 90 ]; then
        echo "$(date): High memory usage: ${memory_usage}%" >> health-alerts.log
    fi
    
    sleep 300  # Check every 5 minutes
done
```

### Documentation and Knowledge Base

#### Runbook Template
```markdown
# Incident: [Type] - [Date]

## Summary
Brief description of the issue

## Timeline
- HH:MM - Issue detected
- HH:MM - Investigation started
- HH:MM - Root cause identified
- HH:MM - Fix implemented
- HH:MM - System restored

## Root Cause
Detailed analysis of what went wrong

## Resolution
Steps taken to resolve the issue

## Lessons Learned
- What went well
- What could be improved
- Preventive measures to implement

## Follow-up Actions
- [ ] Update monitoring
- [ ] Update documentation
- [ ] Implement preventive measures
```

## Getting Help

### Escalation Process

1. **Self-Service (0-15 minutes)**
   - Check this troubleshooting guide
   - Run quick diagnostics
   - Check service logs

2. **Documentation Review (15-30 minutes)**
   - Review architecture documentation
   - Check deployment guide
   - Search knowledge base

3. **Community Support (30-60 minutes)**
   - Check GitHub issues
   - Search Stack Overflow
   - Community forums

4. **Professional Support (1+ hour)**
   - Contact system administrators
   - Engage DevOps team
   - Consider external consultants

### Information to Collect

When reporting issues, include:

```bash
# System information
uname -a
docker --version
docker-compose --version

# Service status
docker ps -a
docker-compose logs --tail=100

# Resource usage
free -h
df -h
docker stats --no-stream

# Network status
docker network ls
netstat -tlpn | head -20

# Configuration (sanitized)
cat .env | sed 's/=.*/=***REDACTED***/'
```

### Contact Information

- **Documentation:** Check `/docs/` directory
- **Issues:** GitHub repository issues
- **Emergency:** Follow incident response procedures

---

**Document Status:** Complete ✅  
**Last Updated:** August 6, 2025  
**Next Review:** September 6, 2025  
**Owner:** AquaScene Engineering Team

**Remember:** When in doubt, create a backup before making any changes!