# Variables
DOCKER_COMPOSE = docker-compose
DOCKER_COMPOSE_SUPERSET = docker-compose -f docker-compose-superset.yml
DATA_DIR = data
SCRIPTS_DIR = scripts
DAGS_DIR = dags
LOGS_DIR = logs
SUPERSET_DIR = superset-init

# Colors for better visibility
YELLOW := "\e[1;33m"
GREEN := "\e[1;32m"
RED := "\e[1;31m"
NC := "\e[0m"

# Initialize directories and permissions safely
.PHONY: init-dirs
init-dirs:
	@echo ${YELLOW}"Creating directories..."${NC}
	@mkdir -p $(DATA_DIR) $(SCRIPTS_DIR) $(DAGS_DIR) $(LOGS_DIR) $(SUPERSET_DIR)
	@touch $(LOGS_DIR)/.gitkeep
	@echo ${GREEN}"Directories created"${NC}

# Set permissions
.PHONY: set-permissions
set-permissions:
	@echo ${YELLOW}"Setting permissions..."${NC}
	@if [ -d "$(LOGS_DIR)" ]; then \
		sudo chown -R $$USER:$$USER $(LOGS_DIR) && \
		sudo chmod -R 777 $(LOGS_DIR); \
	fi
	@if [ -d "$(DATA_DIR)" ]; then \
		sudo chown -R $$USER:$$USER $(DATA_DIR) && \
		sudo chmod -R 777 $(DATA_DIR); \
	fi
	@if [ -d "$(DAGS_DIR)" ]; then \
		sudo chown -R $$USER:$$USER $(DAGS_DIR) && \
		sudo chmod -R 777 $(DAGS_DIR); \
	fi
	@if [ -d "$(SCRIPTS_DIR)" ]; then \
		sudo chown -R $$USER:$$USER $(SCRIPTS_DIR) && \
		sudo chmod -R 777 $(SCRIPTS_DIR); \
	fi
	@echo ${GREEN}"Permissions set"${NC}

# Setup environment variables
.PHONY: setup-env
setup-env:
	@echo ${YELLOW}"Setting up environment variables..."${NC}
	@python3 generate_fernet_key.py
	@if ! grep -q "AIRFLOW_UID" .env; then \
		echo "AIRFLOW_UID=$$(id -u)" >> .env; \
	fi
	@echo ${GREEN}"Environment variables set up successfully"${NC}

# Create Docker network
.PHONY: create-network
create-network:
	@echo ${YELLOW}"Setting up Docker network..."${NC}
	@docker network create app-network 2>/dev/null || true
	@echo ${GREEN}"Network setup complete"${NC}

# Start all services
.PHONY: up
up: create-network
	@echo ${YELLOW}"Starting services..."${NC}
	@$(DOCKER_COMPOSE) up -d
	@echo ${GREEN}"Services started successfully"${NC}

# Stop all services
.PHONY: down
down:
	@echo ${YELLOW}"Stopping services..."${NC}
	@$(DOCKER_COMPOSE) down --remove-orphans
	@echo ${GREEN}"Services stopped"${NC}

# Clean everything
.PHONY: clean
clean:
	@echo ${RED}"Cleaning environment..."${NC}
	@$(DOCKER_COMPOSE) down -v --remove-orphans || true
	@sudo rm -rf $(LOGS_DIR)/* $(DATA_DIR)/* || true
	@docker system prune -f || true
	@docker volume prune -f || true
	@echo ${GREEN}"Environment cleaned"${NC}

# View logs
.PHONY: logs
logs:
	@$(DOCKER_COMPOSE) logs -f

.PHONY: logs-airflow
logs-airflow:
	@$(DOCKER_COMPOSE) logs -f airflow-webserver airflow-scheduler

.PHONY: logs-warehouse
logs-warehouse:
	@$(DOCKER_COMPOSE) logs -f warehouse

# Restart services
.PHONY: restart-airflow
restart-airflow:
	@echo ${YELLOW}"Restarting Airflow..."${NC}
	@$(DOCKER_COMPOSE) restart airflow-webserver airflow-scheduler
	@echo ${GREEN}"Airflow restarted"${NC}

.PHONY: restart-warehouse
restart-warehouse:
	@echo ${YELLOW}"Restarting Warehouse..."${NC}
	@$(DOCKER_COMPOSE) restart warehouse
	@echo ${GREEN}"Warehouse restarted"${NC}

# Show service status
.PHONY: status
status:
	@echo ${YELLOW}"Service Status:"${NC}
	@$(DOCKER_COMPOSE) ps

# Start fresh installation
.PHONY: start-fresh
start-fresh:
	@echo ${YELLOW}"Starting fresh installation..."${NC}
	@make down
	@make clean
	@make init-dirs
	@make set-permissions
	@make setup-env
	@make up
	@echo ${YELLOW}"Waiting for services to initialize..."${NC}
	@sleep 30
	@echo ${GREEN}"==================================="${NC}
	@echo ${GREEN}"Installation complete! Access points:"${NC}
	@echo "Airflow: http://localhost:8080"
	@echo "  Username: admin"
	@echo "  Password: admin"
	@echo ""
	@echo "Adminer: http://localhost:8081"
	@echo "  System: PostgreSQL"
	@echo "  Server: warehouse"
	@echo "  Username: admin"
	@echo "  Password: adminpassword"
	@echo ${GREEN}"==================================="${NC}

# Check service health
.PHONY: health
health:
	@echo ${YELLOW}"Checking service health..."${NC}
	@echo "\nAirflow Webserver:"
	@curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/health || echo "Not responding"
	@echo "\nWarehouse:"
	@docker-compose exec -T warehouse pg_isready -U admin -d myapp || echo "Not responding"

# Help
.PHONY: help
help:
	@echo ${GREEN}"Available commands:"${NC}
	@echo "  make init-dirs        - Create required directories"
	@echo "  make set-permissions  - Set correct permissions"
	@echo "  make up               - Start services"
	@echo "  make down             - Stop services"
	@echo "  make clean            - Clean environment"
	@echo "  make logs             - View all logs"
	@echo "  make logs-airflow     - View Airflow logs"
	@echo "  make logs-warehouse   - View Warehouse logs"
	@echo "  make restart-airflow  - Restart Airflow"
	@echo "  make restart-warehouse - Restart Warehouse"
	@echo "  make status           - Check service status"
	@echo "  make start-fresh      - Clean install"
	@echo "  make health           - Check service health"
	@echo "  make help             - Show this help"

.DEFAULT_GOAL := help