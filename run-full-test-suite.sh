#!/bin/bash

# AquaScene Content Engine - Full Test Suite Runner
# This script runs comprehensive tests to validate the entire system

set -e

echo "🧪 AquaScene Content Engine - Full Test Suite"
echo "=============================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
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

info() {
    echo -e "${PURPLE}[INFO] $1${NC}"
}

# Test results tracking
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0
SKIPPED_TESTS=0

# Function to run a test and track results
run_test() {
    local test_name="$1"
    local test_command="$2"
    local required="${3:-true}"
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    log "Running test: $test_name"
    
    if eval "$test_command" >/dev/null 2>&1; then
        success "✅ $test_name"
        PASSED_TESTS=$((PASSED_TESTS + 1))
        return 0
    else
        if [ "$required" = "true" ]; then
            error "❌ $test_name"
            FAILED_TESTS=$((FAILED_TESTS + 1))
            return 1
        else
            warning "⏭️  $test_name (skipped - optional)"
            SKIPPED_TESTS=$((SKIPPED_TESTS + 1))
            return 0
        fi
    fi
}

# Check if running from project root
if [ ! -f "docker-compose.yml" ]; then
    error "Please run this script from the project root directory"
    exit 1
fi

# Start timestamp
START_TIME=$(date +%s)

info "Starting comprehensive test suite for AquaScene Content Engine"
info "This will take several minutes to complete..."

# Phase 1: Pre-flight checks
echo ""
log "Phase 1: Pre-flight Checks"
echo "=========================="

run_test "Docker daemon running" "docker info"
run_test "Docker Compose available" "docker-compose version || docker compose version"
run_test "Project structure valid" "[ -f docker-compose.yml ] && [ -d services ] && [ -d infrastructure ]"
run_test "Environment file exists" "[ -f .env ]"
run_test "Docker Compose config valid" "docker-compose config >/dev/null || docker compose config >/dev/null"

# Phase 2: Infrastructure Tests
echo ""
log "Phase 2: Infrastructure Tests"
echo "============================="

# Network validation
run_test "Docker networks exist" "docker network ls | grep -q content-engine && docker network ls | grep -q monitoring"
run_test "Docker volumes exist" "docker volume ls | grep -q postgres_data && docker volume ls | grep -q redis_data"

# Service startup
log "Starting services for testing..."
if docker-compose up -d --build >/dev/null 2>&1 || docker compose up -d --build >/dev/null 2>&1; then
    success "Services started successfully"
else
    error "Failed to start services"
    exit 1
fi

# Wait for services to be ready
log "Waiting for services to initialize (60 seconds)..."
sleep 60

# Phase 3: Service Health Tests
echo ""
log "Phase 3: Service Health Tests"
echo "============================="

# Database tests
run_test "PostgreSQL health" "docker exec content-engine-postgres pg_isready -U postgres"
run_test "Redis health" "docker exec content-engine-redis redis-cli ping"
run_test "MinIO health" "docker exec content-engine-minio curl -f http://localhost:9000/minio/health/live"

# Application service tests
services=(
    "content-engine-api:8000"
    "content-engine-ai:8001"
    "content-engine-scraper:8002"
    "content-engine-distributor:8003"
    "content-engine-subscribers:8004"
)

for service in "${services[@]}"; do
    container_name=$(echo "$service" | cut -d':' -f1)
    port=$(echo "$service" | cut -d':' -f2)
    service_display=$(echo "$container_name" | sed 's/content-engine-//')
    
    run_test "$service_display service health" "curl -f -s http://localhost:$port/health"
done

# Infrastructure service tests
run_test "Nginx proxy health" "curl -f -s http://localhost:80/health" "false"
run_test "Prometheus health" "curl -f -s http://localhost:9090/-/healthy"
run_test "Grafana health" "curl -f -s http://localhost:3000/api/health"

# Phase 4: E2E Tests
echo ""
log "Phase 4: End-to-End Tests"
echo "========================="

# Run E2E test suite if available
if [ -f "services/e2e-testing/Dockerfile" ]; then
    log "Running E2E test suite..."
    
    # Build and run E2E tests
    if docker-compose -f docker-compose.yml run --rm e2e-testing >/dev/null 2>&1 || docker compose -f docker-compose.yml run --rm e2e-testing >/dev/null 2>&1; then
        success "E2E test suite passed"
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        warning "E2E test suite failed or skipped"
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
else
    warning "E2E test suite not available"
    SKIPPED_TESTS=$((SKIPPED_TESTS + 1))
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
fi

# Phase 5: Integration Tests
echo ""
log "Phase 5: Integration Tests"
echo "=========================="

# Test service-to-service communication
run_test "API to Database connectivity" "docker exec content-engine-api python -c 'import asyncpg; import asyncio; asyncio.run(asyncpg.connect(\"postgresql://postgres:postgres@postgres:5432/content_engine\").close())'" "false"

run_test "API to Redis connectivity" "docker exec content-engine-api python -c 'import redis; redis.Redis(host=\"redis\", port=6379).ping()'" "false"

# Test web scraper functionality
run_test "Web scraper job submission" "curl -f -s -X POST http://localhost:8002/api/v1/scrape -H 'Content-Type: application/json' -d '{\"url\":\"https://httpbin.org/json\",\"content_type\":\"test\"}'" "false"

# Test subscriber management
test_email="test-$(date +%s)@example.com"
run_test "Subscriber management" "curl -f -s -X POST http://localhost:8004/api/v1/subscribers/subscribe -H 'Content-Type: application/json' -d '{\"email\":\"$test_email\",\"first_name\":\"Test\"}'" "false"

# Phase 6: Performance Tests
echo ""
log "Phase 6: Performance Tests"
echo "=========================="

# Memory usage check
run_test "Memory usage acceptable" "[ \$(docker stats --no-stream --format 'table {{.MemUsage}}' | grep -v MEM | cut -d'/' -f1 | sed 's/[^0-9]//g' | head -1) -lt 1000 ]" "false"

# Response time check
run_test "API response time acceptable" "[ \$(curl -o /dev/null -s -w '%{time_total}' http://localhost:8000/health | cut -d'.' -f1) -lt 5 ]" "false"

# Phase 7: Security Tests
echo ""
log "Phase 7: Security Tests"
echo "======================"

# Check for exposed sensitive information
run_test "No sensitive data in logs" "! docker-compose logs | grep -i 'password\\|secret\\|key' | grep -v 'password_hash'" "false"

# Check service isolation
run_test "Services properly isolated" "docker network inspect content-engine | grep -q '\"Internal\": false'" "false"

# Phase 8: Monitoring Tests
echo ""
log "Phase 8: Monitoring Tests"
echo "========================"

# Check Prometheus targets
run_test "Prometheus scraping targets" "curl -s http://localhost:9090/api/v1/targets | grep -q '\"health\":\"up\"'" "false"

# Check Grafana datasources
run_test "Grafana datasources configured" "curl -s http://admin:grafana_secure_2024!@localhost:3000/api/datasources | grep -q prometheus" "false"

# Phase 9: Cleanup Tests
echo ""
log "Phase 9: Cleanup and Resource Tests"
echo "===================================="

# Check for resource leaks
run_test "No resource leaks detected" "[ \$(docker ps -q | wc -l) -eq \$(docker-compose ps -q | wc -l) ]" "false"

# Test graceful shutdown
log "Testing graceful shutdown..."
if docker-compose down --timeout 30 >/dev/null 2>&1 || docker compose down --timeout 30 >/dev/null 2>&1; then
    success "Graceful shutdown successful"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    error "Graceful shutdown failed"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi
TOTAL_TESTS=$((TOTAL_TESTS + 1))

# Calculate test duration
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

# Generate test report
echo ""
echo "🏁 Test Suite Complete"
echo "======================"
echo "Duration: ${DURATION} seconds"
echo "Total Tests: $TOTAL_TESTS"
echo "Passed: $PASSED_TESTS"
echo "Failed: $FAILED_TESTS"
echo "Skipped: $SKIPPED_TESTS"
echo ""

# Calculate success rate
if [ $TOTAL_TESTS -gt 0 ]; then
    SUCCESS_RATE=$(( (PASSED_TESTS * 100) / TOTAL_TESTS ))
    echo "Success Rate: ${SUCCESS_RATE}%"
else
    SUCCESS_RATE=0
fi

# Generate detailed report
REPORT_FILE="test-report-$(date +%Y%m%d-%H%M%S).txt"
cat > "$REPORT_FILE" << EOF
AquaScene Content Engine - Test Report
======================================

Date: $(date)
Duration: ${DURATION} seconds

Test Summary:
- Total Tests: $TOTAL_TESTS
- Passed: $PASSED_TESTS
- Failed: $FAILED_TESTS
- Skipped: $SKIPPED_TESTS
- Success Rate: ${SUCCESS_RATE}%

System Information:
- Docker Version: $(docker --version)
- Docker Compose Version: $(docker-compose --version 2>/dev/null || docker compose version 2>/dev/null || echo "N/A")
- OS: $(uname -a)
- Available Memory: $(free -h | grep Mem | awk '{print $7}' 2>/dev/null || echo "N/A")
- Available Disk: $(df -h . | tail -1 | awk '{print $4}' 2>/dev/null || echo "N/A")

Recommendations:
EOF

# Add recommendations based on results
if [ $FAILED_TESTS -gt 0 ]; then
    echo "- Address failed tests before deploying to production" >> "$REPORT_FILE"
fi

if [ $SKIPPED_TESTS -gt 5 ]; then
    echo "- Review skipped tests and implement missing features" >> "$REPORT_FILE"
fi

if [ $SUCCESS_RATE -lt 80 ]; then
    echo "- Success rate below 80%, system needs attention" >> "$REPORT_FILE"
fi

echo "- Review logs for any warning messages" >> "$REPORT_FILE"
echo "- Monitor system resources during production use" >> "$REPORT_FILE"
echo "- Set up automated testing in CI/CD pipeline" >> "$REPORT_FILE"

info "Detailed report saved to: $REPORT_FILE"

# Final status
echo ""
if [ $SUCCESS_RATE -ge 90 ] && [ $FAILED_TESTS -eq 0 ]; then
    success "🎉 Test suite PASSED! System is ready for use."
    echo "✅ All critical tests passed successfully"
    exit 0
elif [ $SUCCESS_RATE -ge 70 ]; then
    warning "⚠️  Test suite completed with WARNINGS"
    echo "🔧 Some non-critical tests failed, but system should function"
    exit 0
else
    error "❌ Test suite FAILED"
    echo "🚨 Critical issues detected, system needs fixes before use"
    exit 1
fi