# ---- COMMANDS ----
.PHONY: help build up down restart logs shell frontend-shell backend-shell clean rebuild

help:
	@echo "Available commands:"
	@echo "  make build           Build all Docker images"
	@echo "  make up              Start all services (in background)"
	@echo "  make down            Stop all containers"
	@echo "  make restart         Restart all containers"
	@echo "  make logs            Show logs (follow mode)"
	@echo "  make shell           Open shell in Django backend"
	@echo "  make frontend-shell  Open shell in React frontend"
	@echo "  make rebuild         Rebuild everything (no cache)"
	@echo "  make clean           Stop and remove all containers, images, and volumes"

build:
	docker compose build

up:
	docker compose up -d

down:
	docker compose down

restart:
	docker compose down
	docker compose up -d

logs:
	docker compose logs -f

shell:
	docker compose exec backend bash

frontend-shell:
	docker compose exec frontend sh

rebuild:
	docker compose build --no-cache

clean:
	docker compose down --rmi all --volumes --remove-orphans
