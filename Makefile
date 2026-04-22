PYTHON ?= python3
COMPOSE ?= docker compose

.PHONY: help install lint format test coverage build clean example-env example-build example-migrate example-superuser example-bootstrap example-dev example-up example-down example-logs example-shell

help:
	@echo "Common commands for django-authkit development."
	@echo "  make install       Install package with development dependencies."
	@echo "  make lint          Run static checks."
	@echo "  make format        Format Python code."
	@echo "  make test          Run tests."
	@echo "  make coverage      Run tests with coverage."
	@echo "  make build         Build package artifacts."
	@echo "  make clean         Remove local build and tool cache artifacts."
	@echo "  make example-env   Create .env from .env.example if missing."
	@echo "  make example-build Build the example Django app image."
	@echo "  make example-migrate Run example app migrations."
	@echo "  make example-superuser Create the example dev superuser."
	@echo "  make example-bootstrap Prepare env, image, DB, and superuser."
	@echo "  make example-dev   Bootstrap and start the example app."
	@echo "  make example-up    Start the example Django app container."
	@echo "  make example-down  Stop the example Django app container."
	@echo "  make example-logs  Follow example app logs."
	@echo "  make example-shell Open a shell in the example app container."

install:
	$(PYTHON) -m pip install -e ".[dev]"

lint:
	$(PYTHON) -m ruff check src tests example_django_app
	$(PYTHON) -m black --check src tests example_django_app
	$(PYTHON) -m isort --check-only src tests example_django_app
	$(PYTHON) -m mypy src

format:
	$(PYTHON) -m ruff check --fix src tests example_django_app
	$(PYTHON) -m black src tests example_django_app
	$(PYTHON) -m isort src tests example_django_app

test:
	$(PYTHON) -m pytest

coverage:
	$(PYTHON) -m pytest --cov=authkit --cov-report=term-missing --cov-report=html

build:
	$(PYTHON) -m build

clean:
	rm -rf build dist *.egg-info src/*.egg-info
	rm -rf .pytest_cache .mypy_cache .ruff_cache htmlcov
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	find . -type f \( -name "*.pyc" -o -name "*.pyo" \) -delete

example-env:
	@if [ ! -f .env ]; then cp .env.example .env; echo "Created .env from .env.example"; else echo ".env already exists"; fi

example-build: example-env
	$(COMPOSE) build example

example-migrate: example-env
	$(COMPOSE) run --rm example python manage.py migrate

example-superuser: example-env
	$(COMPOSE) run --rm example python manage.py shell -c "import os; from django.contrib.auth import get_user_model; User = get_user_model(); email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@example.com'); password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'admin12345'); User.objects.filter(email=email).exists() or User.objects.create_superuser(email=email, password=password); print(f'Dev superuser ready: {email}')"

example-bootstrap: example-build example-migrate example-superuser
	@echo "Example app is ready. Run: make example-up"

example-dev: example-bootstrap
	$(COMPOSE) up example

example-up: example-env
	$(COMPOSE) up --build example

example-down:
	$(COMPOSE) down

example-logs:
	$(COMPOSE) logs -f example

example-shell: example-env
	$(COMPOSE) run --rm example sh
