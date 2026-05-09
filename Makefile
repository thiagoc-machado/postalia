SHELL := /bin/sh

COMPOSE_DEV := docker compose -f docker-compose.yml -f docker-compose.dev.yml
COMPOSE_PROD := docker compose -f docker-compose.yml

.PHONY: up up-dev up-prod down reload build build-dev build-prod migrate logs logs-follow shell-back shell-front test-back test-front tests tests-back tests-front lint-back lint-front format-back format-front ps

up:
	@$(COMPOSE_DEV) up --build

up-dev:
	@$(COMPOSE_DEV) up --build

up-prod:
	@$(COMPOSE_PROD) up --build

down:
	@$(COMPOSE_DEV) down

reload:
	@$(COMPOSE_DEV) restart backend frontend celery

build:
	@$(COMPOSE_DEV) build

build-dev:
	@$(COMPOSE_DEV) build

build-prod:
	@$(COMPOSE_PROD) build

migrate:
	@$(COMPOSE_DEV) exec backend python manage.py migrate --noinput

logs:
	@$(COMPOSE_DEV) logs -f --tail=200

logs-follow:
	@$(COMPOSE_DEV) logs -f --tail=200

shell-back:
	@$(COMPOSE_DEV) exec backend sh

shell-front:
	@$(COMPOSE_DEV) exec frontend sh

test-back:
	@$(COMPOSE_DEV) exec backend python -m pytest

test-front:
	@$(COMPOSE_DEV) exec frontend npm run test:run

tests:
	@$(COMPOSE_DEV) exec backend python -m pytest && $(COMPOSE_DEV) exec frontend npm run test:run

tests-back:
	@$(COMPOSE_DEV) exec backend python -m pytest

tests-front:
	@$(COMPOSE_DEV) exec frontend npm run test:run

lint-back:
	@$(COMPOSE_DEV) exec backend ruff check .

lint-front:
	@$(COMPOSE_DEV) exec frontend npm run build

format-back:
	@$(COMPOSE_DEV) exec backend ruff format .

format-front:
	@$(COMPOSE_DEV) exec frontend npm run build

ps:
	@$(COMPOSE_DEV) ps
