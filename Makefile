.ONESHELL:
ENV_PREFIX=$(python3 -c "if __import__('pathlib').Path('.venv/bin/pip').exists(): print('.venv/bin/')")
project_name = $("knowledge_graph" | tr '-' '_')

.PHONY: help
help:             ## Show the help.
	@echo "Usage: make <target>"
	@echo ""
	@echo "Targets:"
	@fgrep "##" Makefile | fgrep -v fgrep


.PHONY: show
show:             ## Show the current environment.
	@echo "Current environment:"
	@echo "Running using $(ENV_PREFIX)"
	@$(ENV_PREFIX)python -V
	@$(ENV_PREFIX)python -m site

.PHONY: install
install:          ## Install the project in dev mode.
	@echo "Don't forget to run 'make virtualenv' if you got errors."
	$(ENV_PREFIX)pip install -e .[test]

.PHONY: build
install:          ## Install the project in dev mode.
	@echo "Build wheel file"
	$(ENV_PREFIX)python -m build

.PHONY: lint
lint:             ## Run pep8, black, mypy linters.
	$(ENV_PREFIX)flake8 src/$(project_name)/
	$(ENV_PREFIX)black -l 79 --check src/$(project_name)/
	$(ENV_PREFIX)black -l 79 --check tests/

.PHONY: test
test: lint        ## Run tests and generate coverage report.
	$(ENV_PREFIX)pytest -v --cov-config .coveragerc --cov=src/$(project_name) -l --tb=short --maxfail=1 tests/
	$(ENV_PREFIX)coverage xml
	$(ENV_PREFIX)coverage html

.PHONY: watch
watch:            ## Run tests on every change.
	ls **/**.py | entr $(ENV_PREFIX)pytest -s -vvv -l --tb=long --maxfail=1 tests/

.PHONY: clean
clean:            ## Clean unused files.
	@find ./ -name '*.pyc' -exec rm -f {} \;
	@find ./ -name '__pycache__' -exec rm -rf {} \;
	@find ./ -name 'Thumbs.db' -exec rm -f {} \;
	@find ./ -name '*~' -exec rm -f {} \;
	@rm -rf .cache
	@rm -rf .pytest_cache
	@rm -rf .mypy_cache
	@rm -rf build
	@rm -rf distsoc_estimation
	@rm -rf *.egg-info
	@rm -rf htmlcov
	@rm -rf .tox/
	@rm -rf docs/_build

.PHONY: virtualenv
virtualenv:       ## Create a virtual environment.
	@echo "creating virtualenv ..."
	@rm -rf .venv
	@python3 -m venv .venv
	@./.venv/bin/pip install -U pip
	@./.venv/bin/pip install -e .[test]
	@echo
	@echo "!!! Please run 'source .venv/bin/activate' to enable the environment !!!"

.PHONY: release
release:          ## Create a new tag for release.
	@echo "WARNING: This operation will create s version tag and push to github"
	@read -p "Version? (provide the next x.y.z semver) : " TAG
	@echo "$${TAG}" > src/$(project_name)/VERSION
	@$(ENV_PREFIX)gitchangelog > HISTORY.md
	@git add $(project_name)/VERSION HISTORY.md
	@git commit -m "release: version $${TAG} 🚀"
	@echo "creating git tag : $${TAG}"
	@git tag $${TAG}
	@git push -u origin HEAD --tags
	@echo "Github Actions will detect the new tag and release the new version."

.PHONY: docs
docs:             ## Build the documentation.
	@echo "building documentation with PyDoc ..."
	@$(ENV_PREFIX)pdoc --force --html src/$(project_name) --output docs/

.PHONY: init
init:             ## Initialize the project based on an application template.
	@./.github/init.sh

# Docker/Neo4j commands
# Environment variable to control which env file to use (default: .env)
ENV_FILE ?= .env

.PHONY: docker-build
docker-build:     ## Build the Docker image.
	@echo "Building Docker image..."
	@docker-compose --env-file $(ENV_FILE) build

.PHONY: docker-up
docker-up:        ## Start Neo4j (ENV_FILE=.env.dev/staging/prod).
	@echo "Starting Neo4j with $(ENV_FILE)..."
	@docker-compose --env-file $(ENV_FILE) up -d
	@echo "Neo4j is starting... Use 'make docker-logs' to check progress"
	@echo "Access Neo4j Browser at http://localhost:7474"

.PHONY: docker-dev
docker-dev:       ## Start Neo4j in development mode.
	@echo "Starting Neo4j in development mode..."
	@docker-compose -f docker-compose.yml -f docker-compose.dev.yml --env-file .env.dev up -d
	@echo "Development environment started!"
	@echo "Neo4j Browser: http://localhost:7474 (neo4j/dev_password_123)"

.PHONY: docker-staging
docker-staging:   ## Start Neo4j in staging mode.
	@echo "Starting Neo4j in staging mode..."
	@docker-compose --env-file .env.staging up -d
	@echo "Staging environment started!"

.PHONY: docker-prod
docker-prod:      ## Start Neo4j in production mode.
	@echo "Starting Neo4j in production mode..."
	@docker-compose -f docker-compose.yml -f docker-compose.prod.yml --env-file .env.prod up -d
	@echo "Production environment started!"
	@echo "⚠️  Make sure you've changed default passwords in .env.prod!"

.PHONY: docker-down
docker-down:      ## Stop Neo4j (ENV_FILE=.env.dev/staging/prod).
	@echo "Stopping Neo4j..."
	@docker compose down

.PHONY: docker-restart
docker-restart:   ## Restart Neo4j.
	@docker-compose restart neo4j

.PHONY: docker-logs
docker-logs:      ## Show Neo4j logs.
	@docker-compose logs -f neo4j

.PHONY: docker-status
docker-status:    ## Check Neo4j status.
	@docker-compose ps
	@echo ""
	@curl -s http://localhost:7474/ > /dev/null && echo "✓ Neo4j is running" || echo "✗ Neo4j is not accessible"

.PHONY: docker-shell
docker-shell:     ## Open a shell in the Neo4j container.
	@docker-compose exec neo4j /bin/bash

.PHONY: docker-cypher
docker-cypher:    ## Open Cypher shell.
	@docker-compose exec neo4j cypher-shell -u neo4j

.PHONY: docker-backup
docker-backup:    ## Create a backup of Neo4j database.
	@echo "Creating backup..."
	@mkdir -p backups
	@docker-compose exec neo4j neo4j-admin database dump neo4j --to-path=/data/backups/backup_$$(date +%Y%m%d_%H%M%S).dump
	@echo "Backup created successfully"

.PHONY: docker-clean
docker-clean:     ## Remove all Neo4j containers and volumes (WARNING: deletes data!).
	@echo "WARNING: This will delete all Neo4j data!"
	@read -p "Are you sure? (y/N): " confirm && [ $$confirm = y ] || exit 1
	@docker-compose down -v
	@echo "Neo4j data cleaned"

.PHONY: docker-monitoring
docker-monitoring: ## Start Neo4j with full monitoring stack.
	@echo "Starting Neo4j with Prometheus and Grafana..."
	@docker-compose --profile with-monitoring up -d
	@echo "Neo4j: http://localhost:7474"
	@echo "Prometheus: http://localhost:9090"
	@echo "Grafana: http://localhost:3000 (admin/admin)"

.PHONY: docker-proxy
docker-proxy:     ## Start Neo4j with Nginx reverse proxy.
	@docker-compose --profile with-proxy up -d

.PHONY: docker-full
docker-full:      ## Start Neo4j with all services (proxy + monitoring).
	@docker-compose --profile with-proxy --profile with-monitoring up -d

# __author__ = 'saradindusengupta'
