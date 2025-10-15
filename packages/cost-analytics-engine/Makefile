# Analyzer Module Makefile (Python)
PYTHON := python3
PIP := pip3
VENV := venv
MODULE_NAME := kcloud-analyzer
DOCKER_IMAGE := kcloud-opt/analyzer
VERSION ?= 0.1.0

.PHONY: help install dev test clean run docker-build

help: ## Show help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-20s %s\n", $$1, $$2}'

install: ## Install dependencies
	$(PYTHON) -m venv $(VENV)
	. $(VENV)/bin/activate && $(PIP) install --upgrade pip
	. $(VENV)/bin/activate && $(PIP) install -r requirements.txt

dev: install ## Setup development environment
	. $(VENV)/bin/activate && $(PIP) install black flake8 mypy pytest-cov
	@cp -n config.example.yaml config.yaml || true

test: ## Run tests
	. $(VENV)/bin/activate && pytest tests/ -v --cov=src --cov-report=html

lint: ## Run linting
	. $(VENV)/bin/activate && black --check src/ tests/
	. $(VENV)/bin/activate && flake8 src/ tests/
	. $(VENV)/bin/activate && mypy src/

format: ## Format code
	. $(VENV)/bin/activate && black src/ tests/

clean: ## Clean up
	rm -rf $(VENV)
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache htmlcov .coverage

run: ## Run the service
	. $(VENV)/bin/activate && python -m src.main

run-api: ## Run API server
	. $(VENV)/bin/activate && uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8001

docker-build: ## Build Docker image
	docker build -t $(DOCKER_IMAGE):$(VERSION) .
	docker tag $(DOCKER_IMAGE):$(VERSION) $(DOCKER_IMAGE):latest

docker-run: ## Run in Docker
	docker run -d --name $(MODULE_NAME) \
		-p 8001:8001 \
		-v $(PWD)/config.yaml:/app/config.yaml \
		--env-file .env \
		$(DOCKER_IMAGE):latest

docker-stop: ## Stop Docker container
	docker stop $(MODULE_NAME) && docker rm $(MODULE_NAME)