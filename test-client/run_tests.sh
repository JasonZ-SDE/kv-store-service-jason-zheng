#!/bin/bash

# Run Test Client Unit Tests
echo "Running Test Client Unit Tests..."
echo "=================================="

# Build the container with test dependencies
echo "Building test environment..."
docker build -t test-client-test .

# Run tests
echo "Running tests..."
docker run --rm test-client-test python -m pytest tests/ -v --tb=short

echo ""
echo "Test run completed."