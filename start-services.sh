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
