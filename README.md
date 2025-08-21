# Key-Value Store Demo System

A microservices-based key-value store built with FastAPI, featuring a main storage service and a validation test client. The system demonstrates modern containerized architecture with comprehensive testing and monitoring capabilities.

## 🏗️ Architecture Overview

```
┌─────────────────┐    HTTP/JSON    ┌─────────────────┐
│   Test Client   │◄──────────────►│   KV Service    │
│   (Port 8001)   │                 │   (Port 8000)   │
└─────────────────┘                 └─────────────────┘
│                                   │
│ • Validation Tests                │ • Key-Value Storage
│ • Workflow Testing                │ • CRUD Operations
│ • Health Monitoring               │ • Thread-Safe Access
│ • Status Reporting                │ • Health Monitoring
```

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.12+ (for local development)
- Git

### Using Docker (Recommended)

1. **Clone the repository:**

   ```bash
   git clone https://github.com/JasonZ-SDE/kv-store-service.git
   cd kv-store-service
   ```

2. **Start all services:**

   ```bash
   docker compose up --build
   ```

3. **Verify services are running:**

   ```bash
   # Check KV Service health
   curl http://localhost:8000/health

   # Check Test Client health
   curl http://localhost:8001/health
   ```

4. **View API documentation:**
   - KV Service: http://localhost:8000/docs
   - Test Client: http://localhost:8001/docs

### Using Makefile

```bash
# Start services in background
make up

# View logs
make logs

# Stop services
make down

# Run tests
make test
```

## 📋 API Reference

### KV Service (Port 8000)

#### Store/Update Key-Value Pair

```bash
# Store new value
curl -X POST http://localhost:8000/keys/mykey \
  -H "Content-Type: application/json" \
  -d '{"key": "mykey", "value": "myvalue"}'

# Update existing value
curl -X PUT http://localhost:8000/keys/mykey \
  -H "Content-Type: application/json" \
  -d '{"key": "mykey", "value": "newvalue"}'
```

#### Retrieve Value

```bash
curl http://localhost:8000/keys/mykey
```

#### Delete Key

```bash
curl -X DELETE http://localhost:8000/keys/mykey
```

#### Health Check

```bash
curl http://localhost:8000/health
```

### Test Client (Port 8001)

#### Run Deletion Test

```bash
curl -X POST http://localhost:8001/test/deletion
```

#### Run Overwrite Test

```bash
curl -X POST http://localhost:8001/test/overwrite
```

#### Check Service Status

```bash
curl http://localhost:8001/test/status
```

## 🧪 Testing

### Quick Test Commands

```bash
# Run all tests using Makefile
make test

# Or run individually
cd kv-service && ./run_tests.sh
cd test-client && ./run_tests.sh
```

### Unit Tests

Both services include comprehensive unit test suites:

#### KV Service Tests

```bash
# Using Docker
cd kv-service && ./run_tests.sh

# Local development
cd kv-service && python -m pytest tests/ -v --cov=. --cov-report=html

# Run specific tests
python -m pytest tests/test_main.py::TestStoreKey -v
python -m pytest tests/test_main.py::TestStoreKey::test_store_key_success -v
```

**Coverage:** 86% (19 tests)

- Health endpoint functionality
- Value model validation and JSON serialization
- Complete CRUD operations (Create, Read, Update, Delete)
- Error handling and validation
- Concurrent access and thread safety
- Complete workflows and edge cases

#### Test Client Tests

```bash
# Using Docker
cd test-client && ./run_tests.sh

# Local development
cd test-client && python -m pytest tests/ -v --cov=. --cov-report=html

# Run specific workflow tests
python -m pytest tests/test_main.py::TestDeletionWorkflow -v
python -m pytest tests/test_main.py::TestOverwriteWorkflow -v
```

**Coverage:** 89% (17 tests)

- Health and status endpoints
- Response model validation
- Deletion and overwrite workflows
- Error handling scenarios (timeouts, failures)
- HTTP client mocking and external service simulation
- Application lifecycle events

### Integration Testing

Test complete service-to-service communication:

```bash
# Start services
docker compose up -d

# Wait for services to be ready
sleep 5

# Test service health
curl http://localhost:8000/health
curl http://localhost:8001/health

# Run automated integration tests
curl -X POST http://localhost:8001/test/deletion
curl -X POST http://localhost:8001/test/overwrite

# Expected successful response:
# {"success": true, "test_name": "test_deletion", "details": {"steps_executed": 4, "all_assertions_passed": true}}

# Cleanup
docker compose down
```

### Manual Testing Examples

#### Basic CRUD Operations

```bash
# Store a key-value pair
curl -X POST http://localhost:8000/keys/mykey \
  -H "Content-Type: application/json" \
  -d '{"key": "mykey", "value": "hello world"}'

# Retrieve the value
curl http://localhost:8000/keys/mykey

# Update the value
curl -X PUT http://localhost:8000/keys/mykey \
  -H "Content-Type: application/json" \
  -d '{"key": "mykey", "value": "updated value"}'

# Delete the key
curl -X DELETE http://localhost:8000/keys/mykey

# Verify deletion (should return 404)
curl http://localhost:8000/keys/mykey
```

#### Complex Data Types

```bash
# Store JSON object
curl -X POST http://localhost:8000/keys/user1 \
  -H "Content-Type: application/json" \
  -d '{"key": "user1", "value": {"name": "John", "age": 30, "active": true}}'

# Store array
curl -X POST http://localhost:8000/keys/scores \
  -H "Content-Type: application/json" \
  -d '{"key": "scores", "value": [85, 92, 78, 96]}'
```

#### Error Testing

```bash
# Test key mismatch (should return 400)
curl -X POST http://localhost:8000/keys/mykey \
  -H "Content-Type: application/json" \
  -d '{"key": "differentkey", "value": "test"}'

# Test missing key (should return 404)
curl http://localhost:8000/keys/nonexistent
```

### Test Coverage Reports

```bash
# Generate HTML coverage reports
cd kv-service && python -m pytest tests/ --cov=. --cov-report=html
cd test-client && python -m pytest tests/ --cov=. --cov-report=html

# View reports in browser
open kv-service/htmlcov/index.html
open test-client/htmlcov/index.html
```

## 🛠️ Local Development

### Setup

1. **Create virtual environment:**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies:**

   ```bash
   # For KV Service
   cd kv-service && pip install -r requirements.txt

   # For Test Client
   cd test-client && pip install -r requirements.txt
   ```

3. **Run services locally:**

   ```bash
   # Terminal 1 - KV Service
   cd kv-service && python main.py

   # Terminal 2 - Test Client (set KV_SERVICE_URL)
   cd test-client && KV_SERVICE_URL=http://localhost:8000 python main.py
   ```

### Environment Variables

#### KV Service

- `PORT`: Service port (default: 8000)
- `HOST`: Service host (default: 0.0.0.0)

#### Test Client

- `PORT`: Service port (default: 8001)
- `HOST`: Service host (default: 0.0.0.0)
- `KV_SERVICE_URL`: KV Service endpoint (default: http://kv-service:8000)

## Monitoring

The system includes comprehensive logging for:

- Request/response timing
- Error tracking and debugging
- Service health monitoring
- Performance metrics

View logs:

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f kv-service
docker compose logs -f test-client
```

## 🔧 Troubleshooting

### Common Issues

1. **Port conflicts:**

   ```bash
   # Check if ports are in use
   lsof -i :8000
   lsof -i :8001

   # Kill processes if needed
   docker compose down
   ```

2. **Service communication errors:**

   ```bash
   # Verify network connectivity
   docker compose exec test-client curl http://kv-service:8000/health
   ```

3. **Database reset:**
   ```bash
   # Restart services to clear in-memory storage
   docker compose restart kv-service
   ```

### Debug Mode

Enable detailed logging:

```bash
# Set log level to DEBUG
docker compose up --build -e LOG_LEVEL=DEBUG
```

## 🏗️ Project Structure

```
kv-store-service/
├── kv-service/              # Main key-value store service
│   ├── main.py             # FastAPI application
│   ├── models.py           # Pydantic models and exceptions
│   ├── requirements.txt    # Python dependencies
│   ├── Dockerfile         # Container configuration
│   ├── pytest.ini        # Test configuration
│   ├── run_tests.sh      # Test runner script
│   └── tests/            # Unit tests
│       ├── __init__.py
│       └── test_main.py
│
├── test-client/            # Test validation service
│   ├── main.py            # FastAPI test client
│   ├── models.py           # Pydantic response models
│   ├── requirements.txt   # Python dependencies
│   ├── Dockerfile        # Container configuration
│   ├── pytest.ini       # Test configuration
│   ├── run_tests.sh     # Test runner script
│   └── tests/           # Unit tests
│       ├── __init__.py
│       └── test_main.py
│
├── docker-compose.yml      # Multi-service orchestration
├── Makefile               # Build automation
├── CLAUDE.md             # Development guidance
├── TASK.md              # Project task tracking
├── PRD.md              # Product requirements
└── README.md          # This file
```

---
