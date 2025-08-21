.PHONY: build up down logs test clean help

help:
	@echo "Available commands:"
	@echo "  build    - Build all Docker images"
	@echo "  up       - Start all services"
	@echo "  down     - Stop all services"
	@echo "  logs     - View logs from all services"
	@echo "  test     - Run deletion and overwrite tests"
	@echo "  clean    - Remove all containers and images"
	@echo "  help     - Show this help message"

build:
	docker compose build

up:
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f

test:
	@echo "Running deletion test..."
	curl -X POST http://localhost:8001/test/deletion
	@echo ""
	@echo "Running overwrite test..."
	curl -X POST http://localhost:8001/test/overwrite

clean:
	docker compose down -v --rmi all --remove-orphans

dev:
	docker compose up --build