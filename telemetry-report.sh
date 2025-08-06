#\!/bin/bash

echo "📊 AquaScene Content Engine - Telemetry Report"
echo "=============================================="

# System Metrics
echo ""
echo "🖥️  System Performance Metrics:"
echo "------------------------------"
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}" | head -10

# Service Health Status  
echo ""
echo "🏥 Service Health Status:"
echo "------------------------"
echo "✅ PostgreSQL: $(docker exec content-engine-postgres pg_isready -U postgres 2>/dev/null || echo 'DOWN')"
echo "✅ Redis: $(docker exec content-engine-redis redis-cli ping 2>/dev/null || echo 'DOWN')"
echo "✅ Content Manager: $(curl -s http://localhost:8000/health | jq -r '.status' 2>/dev/null || echo 'DOWN')"
echo "✅ MinIO: $(curl -s http://localhost:9000/minio/health/live 2>/dev/null && echo 'UP' || echo 'DOWN')"
echo "✅ Prometheus: $(curl -s http://localhost:9090/-/healthy 2>/dev/null && echo 'UP' || echo 'DOWN')"
echo "✅ Grafana: $(curl -s http://localhost:3000/api/health | jq -r '.database' 2>/dev/null || echo 'DOWN')"

# Performance Metrics
echo ""
echo "⚡ Performance Metrics:"
echo "----------------------"
echo "API Response Time: $(curl -w '%{time_total}' -s -o /dev/null http://localhost:8000/health)s"
echo "Database Query Time: $(docker exec content-engine-postgres psql -U postgres -d content_engine -c '\timing on' -c 'SELECT NOW();' 2>/dev/null | grep Time | tail -1 || echo 'N/A')"

# Resource Usage
echo ""
echo "💾 Resource Utilization:"
echo "-----------------------"
docker system df

echo ""
echo "🔍 Active Services:"
echo "------------------"
docker-compose ps --format "table {{.Service}}\t{{.State}}\t{{.Status}}"

