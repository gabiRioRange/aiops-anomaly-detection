# Makefile para facilitar comandos de desenvolvimento

.PHONY: install install-dev test test-cov lint format clean run docker-build docker-run help

# Instalar dependências básicas
install:
	pip install -e .

# Instalar dependências de desenvolvimento
install-dev:
	pip install -e ".[dev]"

# Executar testes
test:
	pytest tests/ -v

# Executar testes com cobertura
test-cov:
	pytest tests/ --cov=app --cov-report=html --cov-report=term

# Executar linting
lint:
	ruff check app/ tests/

# Formatar código
format:
	black app/ tests/
	ruff check --fix app/ tests/

# Limpar arquivos temporários
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	rm -rf .pytest_cache
	rm -rf .coverage
	rm -rf htmlcov

# Executar aplicação
run:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Build Docker
docker-build:
	docker-compose build

# Run Docker
docker-run:
	docker-compose up

# Help
help:
	@echo "Comandos disponíveis:"
	@echo "  install      - Instalar dependências básicas"
	@echo "  install-dev  - Instalar dependências de desenvolvimento"
	@echo "  test         - Executar testes"
	@echo "  test-cov     - Executar testes com cobertura"
	@echo "  lint         - Executar linting"
	@echo "  format       - Formatar código"
	@echo "  clean        - Limpar arquivos temporários"
	@echo "  run          - Executar aplicação"
	@echo "  docker-build - Build Docker"
	@echo "  docker-run   - Run Docker"