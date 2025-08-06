#!/bin/bash

# AquaScene Content Engine - Network Validation Script
# This script validates Docker networks and service connectivity

set -e

echo "🌐 AquaScene Content Engine - Network Validation"
echo "================================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
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

# Check Docker availability
if ! docker info >/dev/null 2>&1; then
    error "Docker is not running. Please start Docker and try again."
    exit 1
fi

# Validate Docker Compose configuration
log "Validating Docker Compose configuration..."
if docker-compose config >/dev/null 2>&1 || docker compose config >/dev/null 2>&1; then
    success "Docker Compose configuration is valid"
else
    error "Docker Compose configuration is invalid"
    exit 1
fi

# Check required networks
log "Checking Docker networks..."
required_networks=("content-engine" "monitoring")
network_issues=()

for network in "${required_networks[@]}"; do
    if docker network ls | grep -q "$network"; then
        success "Network '$network' exists"
        
        # Inspect network for issues
        network_info=$(docker network inspect "$network" 2>/dev/null)
        if [ $? -eq 0 ]; then
            # Check if network has proper configuration
            driver=$(echo "$network_info" | grep '"Driver"' | head -1 | cut -d'"' -f4)
            if [ "$driver" = "bridge" ]; then
                success "Network '$network' has correct driver: $driver"
            else
                warning "Network '$network' has unexpected driver: $driver"
            fi
        fi
    else
        error "Network '$network' does not exist"
        network_issues+=("$network")
    fi
done

# Create missing networks
if [ ${#network_issues[@]} -gt 0 ]; then
    log "Creating missing networks..."
    for network in "${network_issues[@]}"; do
        log "Creating network: $network"
        docker network create "$network" --driver bridge
        if [ $? -eq 0 ]; then
            success "Created network: $network"
        else
            error "Failed to create network: $network"
        fi
    done
fi

# Check if services are running
log "Checking service status..."
services=(
    "postgres:content-engine-postgres"
    "redis:content-engine-redis"
    "content-manager:content-engine-api"
    "ai-processor:content-engine-ai"
    "web-scraper:content-engine-scraper"
    "subscriber-manager:content-engine-subscribers"
    "distributor:content-engine-distributor"
    "admin-dashboard:content-engine-admin"
    "nginx:content-engine-nginx"
    "prometheus:content-engine-prometheus"
    "grafana:content-engine-grafana"
)

running_services=0
total_services=${#services[@]}

for service in "${services[@]}"; do
    service_name=$(echo "$service" | cut -d':' -f1)
    container_name=$(echo "$service" | cut -d':' -f2)
    
    if docker ps --format "table {{.Names}}" | grep -q "^$container_name$"; then
        success "Service '$service_name' is running"
        running_services=$((running_services + 1))
    else
        warning "Service '$service_name' is not running"
    fi
done

log "Services running: $running_services/$total_services"

# Test network connectivity between services (if running)
if [ $running_services -gt 0 ]; then
    log "Testing network connectivity..."
    
    # Test database connections
    if docker ps --format "table {{.Names}}" | grep -q "content-engine-postgres"; then
        log "Testing PostgreSQL connectivity..."
        if docker exec content-engine-postgres pg_isready -U postgres >/dev/null 2>&1; then
            success "PostgreSQL is accepting connections"
        else
            error "PostgreSQL is not accepting connections"
        fi
    fi
    
    if docker ps --format "table {{.Names}}" | grep -q "content-engine-redis"; then
        log "Testing Redis connectivity..."
        if docker exec content-engine-redis redis-cli ping >/dev/null 2>&1; then
            success "Redis is accepting connections"
        else
            error "Redis is not accepting connections"
        fi
    fi
    
    # Test HTTP service connectivity
    http_services=(
        "content-engine-api:8000"
        "content-engine-ai:8001"
        "content-engine-scraper:8002"
        "content-engine-distributor:8003"
        "content-engine-subscribers:8004"
    )
    
    for service in "${http_services[@]}"; do
        container_name=$(echo "$service" | cut -d':' -f1)
        port=$(echo "$service" | cut -d':' -f2)
        
        if docker ps --format "table {{.Names}}" | grep -q "^$container_name$"; then
            log "Testing HTTP connectivity for $container_name..."
            if docker exec "$container_name" curl -f -s "http://localhost:$port/health" >/dev/null 2>&1; then
                success "$container_name health check passed"
            else
                warning "$container_name health check failed (service may still be starting)"
            fi
        fi
    done
    
    # Test proxy connectivity
    if docker ps --format "table {{.Names}}" | grep -q "content-engine-nginx"; then
        log "Testing Nginx proxy..."
        if docker exec content-engine-nginx nginx -t >/dev/null 2>&1; then
            success "Nginx configuration is valid"
        else
            error "Nginx configuration is invalid"
        fi
    fi
fi

# Check port conflicts
log "Checking for port conflicts..."
ports=(
    "3001:admin-dashboard"
    "8000:content-manager"
    "8001:ai-processor"
    "8002:web-scraper"
    "8003:distributor"
    "8004:subscriber-manager"
    "5432:postgres"
    "6379:redis"
    "9000:minio"
    "9090:prometheus"
    "3000:grafana"
    "80:nginx"
    "443:nginx-ssl"
)

for port_info in "${ports[@]}"; do
    port=$(echo "$port_info" | cut -d':' -f1)
    service=$(echo "$port_info" | cut -d':' -f2)
    
    if netstat -tlnp 2>/dev/null | grep -q ":$port " || ss -tlnp 2>/dev/null | grep -q ":$port "; then
        # Check if it's our Docker container
        if docker ps --format "table {{.Ports}}" | grep -q "0.0.0.0:$port->"; then
            success "Port $port is correctly used by $service"
        else
            warning "Port $port is in use by another process (may conflict with $service)"
        fi
    else
        log "Port $port is available for $service"
    fi
done

# Network performance test (if services are running)
if [ $running_services -gt 2 ]; then
    log "Running network performance tests..."
    
    # Test latency between services
    if docker ps --format "table {{.Names}}" | grep -q "content-engine-api"; then
        if docker ps --format "table {{.Names}}" | grep -q "content-engine-postgres"; then
            log "Testing latency between API and database..."
            latency=$(docker exec content-engine-api ping -c 3 postgres 2>/dev/null | grep "avg" | cut -d'/' -f5 || echo "N/A")
            if [ "$latency" != "N/A" ]; then
                success "Average latency to database: ${latency}ms"
                
                # Warn if latency is high
                if (( $(echo "$latency > 100" | bc -l) )); then
                    warning "High latency detected between services"
                fi
            fi
        fi
    fi
fi

# DNS resolution test
log "Testing DNS resolution within networks..."
if docker ps --format "table {{.Names}}" | grep -q "content-engine-api"; then
    # Test if service can resolve other service names
    services_to_resolve=("postgres" "redis" "ai-processor" "web-scraper")
    
    for service in "${services_to_resolve[@]}"; do
        if docker exec content-engine-api nslookup "$service" >/dev/null 2>&1; then
            success "DNS resolution for '$service' successful"
        else
            warning "DNS resolution for '$service' failed"
        fi
    done
fi

# Check resource usage
log "Checking network resource usage..."
if command -v iftop >/dev/null 2>&1; then
    log "Network monitoring tools are available"
else
    warning "Consider installing network monitoring tools (iftop, netstat, ss)"
fi

# Generate network diagram (if graphviz is available)
if command -v dot >/dev/null 2>&1; then
    log "Generating network diagram..."
    cat > network-diagram.dot << 'EOF'
digraph AquaSceneNetwork {
    rankdir=TB;
    node [shape=box];
    
    // External
    Internet [shape=ellipse, color=blue];
    
    // Load Balancer
    nginx [label="Nginx\nProxy", color=orange];
    
    // Application Services
    subgraph cluster_app {
        label="Application Layer";
        api [label="Content\nManager"];
        ai [label="AI\nProcessor"];
        scraper [label="Web\nScraper"];
        distributor [label="Content\nDistributor"];
        subscriber [label="Subscriber\nManager"];
        admin [label="Admin\nDashboard"];
    }
    
    // Data Layer
    subgraph cluster_data {
        label="Data Layer";
        postgres [label="PostgreSQL", color=green];
        redis [label="Redis", color=red];
        minio [label="MinIO", color=purple];
    }
    
    // Monitoring
    subgraph cluster_monitor {
        label="Monitoring";
        prometheus [label="Prometheus"];
        grafana [label="Grafana"];
        loki [label="Loki"];
    }
    
    // Connections
    Internet -> nginx;
    nginx -> api;
    nginx -> admin;
    
    api -> postgres;
    api -> redis;
    api -> minio;
    
    ai -> postgres;
    ai -> redis;
    
    scraper -> postgres;
    scraper -> redis;
    
    distributor -> postgres;
    distributor -> redis;
    
    subscriber -> postgres;
    subscriber -> redis;
    
    prometheus -> api;
    prometheus -> ai;
    prometheus -> scraper;
    grafana -> prometheus;
}
EOF
    
    dot -Tpng network-diagram.dot -o network-diagram.png 2>/dev/null && success "Network diagram generated: network-diagram.png" || warning "Failed to generate network diagram"
fi

# Summary
echo ""
echo "📊 Network Validation Summary:"
echo "=============================="
echo "- Networks: ${#required_networks[@]} checked"
echo "- Services: $running_services/$total_services running"
echo "- Ports: ${#ports[@]} checked"
echo ""

if [ ${#network_issues[@]} -eq 0 ] && [ $running_services -gt $((total_services / 2)) ]; then
    success "Network validation completed successfully!"
    echo "✅ All critical network components are properly configured"
else
    warning "Network validation completed with issues"
    echo "⚠️  Some network components need attention"
    if [ ${#network_issues[@]} -gt 0 ]; then
        echo "   - Missing networks: ${network_issues[*]}"
    fi
    if [ $running_services -le $((total_services / 2)) ]; then
        echo "   - Only $running_services/$total_services services are running"
    fi
fi

echo ""
echo "🔍 Recommendations:"
echo "- Ensure all services are running: docker-compose up -d"
echo "- Check service logs for connectivity issues: docker-compose logs [service]"
echo "- Monitor network performance: docker stats"
echo "- Use './run-full-test-suite.sh' for end-to-end testing"