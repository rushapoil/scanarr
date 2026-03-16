.PHONY: help build up down dev test lint type-check clean hash

help: ## Show available commands
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

# ── Docker ────────────────────────────────────────────────────────────────────

build: ## Build the production Docker image
	docker compose build

up: ## Start production container (builds if needed)
	docker compose up -d --build

down: ## Stop and remove containers
	docker compose down

dev: ## Start development environment (hot-reload)
	docker compose -f docker-compose.dev.yml up --build

logs: ## Follow container logs
	docker compose logs -f

# ── Development (local, no Docker) ────────────────────────────────────────────

backend-install: ## Install backend Python dependencies
	cd backend && pip install -r requirements.txt

backend-dev: ## Run backend with hot-reload (requires venv)
	cd backend && mkdir -p ../config && alembic upgrade head && uvicorn app.main:app --reload --port 8000

frontend-install: ## Install frontend Node dependencies
	cd frontend && npm install

frontend-dev: ## Run frontend dev server
	cd frontend && npm run dev

# ── Quality ───────────────────────────────────────────────────────────────────

test: ## Run backend tests
	cd backend && pytest tests/ -v

lint: ## Lint backend (ruff) and frontend (eslint)
	cd backend && ruff check app/ tests/
	cd frontend && npm run lint

type-check: ## Type-check frontend
	cd frontend && npm run type-check

# ── Utilities ─────────────────────────────────────────────────────────────────

hash: ## Generate a bcrypt password hash (usage: make hash PASS=yourpassword)
	@docker run --rm python:3.12-slim \
		python -c "from passlib.context import CryptContext; print(CryptContext(['bcrypt']).hash('$(PASS)'))"

clean: ## Remove build artefacts
	rm -rf frontend/dist
	find backend -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find backend -name "*.pyc" -delete
