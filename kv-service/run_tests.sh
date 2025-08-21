#!/bin/bash

# Run KV Service Unit Tests
echo "Running KV Service Unit Tests..."
echo "=================================="

# Build the container with test dependencies
echo "Building test environment..."
docker build -t kv-service-test .

# Run tests
echo "Running tests..."
docker run --rm kv-service-test python -m pytest tests/ -v --tb=short

echo ""
echo "Test run completed."