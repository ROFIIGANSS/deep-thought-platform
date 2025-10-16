.PHONY: help setup proto-compile build up down restart status logs test clean rebuild dev quick-start

# ============================================================================
# Help
# ============================================================================

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-25s %s\n", $$1, $$2}'

# ============================================================================
# Setup & Build
# ============================================================================

setup: ## Run initial setup (venv, deps, proto compilation)
	@echo "Running setup..."
	@bash scripts/setup.sh

proto-compile: ## Compile Protocol Buffer definitions
	@echo "Compiling proto files..."
	@bash scripts/compile_proto.sh

build: ## Build all Docker images
	@echo "Building Docker images..."
	docker-compose build

rebuild: down build up ## Rebuild and restart all services

# ============================================================================
# Service Management
# ============================================================================

up: ## Start all services
	@echo "Starting services..."
	docker-compose up -d
	@echo "Waiting for services to be healthy..."
	@sleep 5
	@docker-compose ps

down: ## Stop all services
	@echo "Stopping services..."
	docker-compose down

restart: ## Restart all services
	@echo "Restarting services..."
	docker-compose restart

status: ## Show status of all services
	@echo "Service Status:"
	@docker-compose ps

# ============================================================================
# Logs
# ============================================================================

logs: ## Show logs from all services
	docker-compose logs -f

logs-router: ## Show MCP Router logs
	docker-compose logs -f mcp-router

logs-consul: ## Show Consul logs
	docker-compose logs -f consul

logs-haproxy: ## Show HAProxy logs
	docker-compose logs -f haproxy

logs-echo: ## Show Echo Agent logs
	docker-compose logs -f echo-agent

logs-weather: ## Show Weather Tool logs
	docker-compose logs -f weather-tool

logs-itinerary: ## Show Itinerary Worker logs
	docker-compose logs -f itinerary-worker

logs-catalog-api: ## Show Catalog API logs
	docker-compose logs -f catalog-api

logs-catalog-ui: ## Show Catalog UI logs
	docker-compose logs -f catalog-ui

# ============================================================================
# User Interfaces
# ============================================================================

ui-consul: ## Open Consul UI in browser
	@echo "Opening Consul UI..."
	@open http://localhost:8500 || xdg-open http://localhost:8500 || echo "Please open http://localhost:8500 in your browser"

ui-haproxy: ## Open HAProxy stats dashboard in browser
	@echo "Opening HAProxy Stats Dashboard..."
	@open http://localhost:8404 || xdg-open http://localhost:8404 || echo "Please open http://localhost:8404 in your browser"

ui-catalog: ## Open Catalog UI in browser
	@echo "Opening Catalog UI..."
	@open http://localhost:8080 || xdg-open http://localhost:8080 || echo "Please open http://localhost:8080 in your browser"

# ============================================================================
# Testing
# ============================================================================

test: ## Run test client
	@echo "Running tests..."
	@source venv/bin/activate && python scripts/test_client.py

# ============================================================================
# Scaling
# ============================================================================

scale-router: ## Scale MCP Router (usage: make scale-router N=3)
	@echo "Scaling MCP Router to $(N) instances..."
	docker-compose up -d --scale mcp-router=$(N) --no-recreate
	@echo "View HAProxy stats: make ui-haproxy"
	@echo "View Consul registry: make consul-check"

scale-echo: ## Scale Echo Agent (usage: make scale-echo N=3)
	@echo "Scaling Echo Agent to $(N) instances..."
	docker-compose up -d --scale echo-agent=$(N) --no-recreate

scale-weather: ## Scale Weather Tool (usage: make scale-weather N=3)
	@echo "Scaling Weather Tool to $(N) instances..."
	docker-compose up -d --scale weather-tool=$(N) --no-recreate

scale-itinerary: ## Scale Itinerary Worker (usage: make scale-itinerary N=3)
	@echo "Scaling Itinerary Worker to $(N) instances..."
	docker-compose up -d --scale itinerary-worker=$(N) --no-recreate

scale-all: ## Scale all scalable services (usage: make scale-all N=3)
	@echo "Scaling all services to $(N) instances..."
	docker-compose up -d --scale mcp-router=$(N) --scale echo-agent=$(N) --scale weather-tool=$(N) --scale itinerary-worker=$(N) --no-recreate
	@echo "View HAProxy stats: make ui-haproxy"
	@echo "View Consul registry: make consul-check"

scale-down: ## Scale all services back to 1 instance
	@echo "Scaling down all services to 1 instance..."
	docker-compose up -d --scale mcp-router=1 --scale echo-agent=1 --scale weather-tool=1 --scale itinerary-worker=1 --no-recreate

# ============================================================================
# Consul Operations
# ============================================================================

consul-check: ## Check services registered in Consul
	@echo "Services registered in Consul:"
	@echo ""
	@echo "=== MCP Routers ==="
	@curl -s http://localhost:8500/v1/health/service/mcp-router | python3 -c "import sys, json; data = json.load(sys.stdin); [print(f\"  {s['Service']['ID']} - {s['Service']['Address']}:{s['Service']['Port']} - {s['Checks'][1]['Status'] if len(s['Checks']) > 1 else 'unknown'}\") for s in data]" 2>/dev/null || echo "  (none or error)"
	@echo ""
	@echo "=== MCP Servers (Cursor Integration) ==="
	@curl -s http://localhost:8500/v1/health/service/mcp-server | python3 -c "import sys, json; data = json.load(sys.stdin); [print(f\"  {s['Service']['ID']} - {s['Service']['Address']}:{s['Service']['Port']} - {s['Checks'][1]['Status'] if len(s['Checks']) > 1 else 'unknown'}\") for s in data]" 2>/dev/null || echo "  (none or error)"
	@echo ""
	@echo "=== Echo Agents ==="
	@curl -s http://localhost:8500/v1/health/service/agent-echo | python3 -c "import sys, json; data = json.load(sys.stdin); [print(f\"  {s['Service']['ID']} - {s['Service']['Address']}:{s['Service']['Port']} - {s['Checks'][1]['Status'] if len(s['Checks']) > 1 else 'unknown'}\") for s in data]" 2>/dev/null || echo "  (none or error)"
	@echo ""
	@echo "=== Weather Tools ==="
	@curl -s http://localhost:8500/v1/health/service/tool-weather | python3 -c "import sys, json; data = json.load(sys.stdin); [print(f\"  {s['Service']['ID']} - {s['Service']['Address']}:{s['Service']['Port']} - {s['Checks'][1]['Status'] if len(s['Checks']) > 1 else 'unknown'}\") for s in data]" 2>/dev/null || echo "  (none or error)"
	@echo ""
	@echo "=== Itinerary Workers ==="
	@curl -s http://localhost:8500/v1/health/service/worker-itinerary | python3 -c "import sys, json; data = json.load(sys.stdin); [print(f\"  {s['Service']['ID']} - {s['Service']['Address']}:{s['Service']['Port']} - {s['Checks'][1]['Status'] if len(s['Checks']) > 1 else 'unknown'}\") for s in data]" 2>/dev/null || echo "  (none or error)"

consul-cleanup: ## Clean up stale Consul service registrations
	@bash scripts/cleanup_consul.sh stale

consul-purge: ## Purge ALL Consul data (WARNING: destructive)
	@bash scripts/cleanup_consul.sh purge

# ============================================================================
# MCP Service Discovery
# ============================================================================

mcp-query: ## Query available MCP services (agents, tools, workers)
	@source venv/bin/activate && python scripts/query_mcp.py all

mcp-query-agents: ## Query available agents
	@source venv/bin/activate && python scripts/query_mcp.py agents

mcp-query-tools: ## Query available tools
	@source venv/bin/activate && python scripts/query_mcp.py tools

mcp-query-workers: ## Query available workers
	@source venv/bin/activate && python scripts/query_mcp.py workers

mcp-query-json: ## Query all services and output as JSON
	@source venv/bin/activate && python scripts/query_mcp.py all --json

# ============================================================================
# MCP Server (Cursor Integration via HAProxy)
# ============================================================================

mcp-server-logs: ## View MCP server logs
	docker-compose logs -f mcp-server

mcp-server-build: ## Build MCP server Docker image
	docker-compose build mcp-server

mcp-server-restart: ## Restart MCP server
	docker-compose restart mcp-server

scale-mcp: ## Scale MCP server instances (usage: make scale-mcp N=3)
	@if [ -z "$(N)" ]; then \
		echo "Usage: make scale-mcp N=<number>"; \
		echo "Example: make scale-mcp N=3"; \
		exit 1; \
	fi
	@echo "Scaling MCP Server to $(N) instances..."
	docker-compose up -d --scale mcp-server=$(N) --no-recreate

# ============================================================================
# Catalog Services
# ============================================================================

catalog-build: ## Build catalog services (API + UI)
	@echo "Building catalog services..."
	docker-compose build catalog-api catalog-ui

catalog-up: ## Start catalog services
	@echo "Starting catalog services..."
	docker-compose up -d catalog-api catalog-ui
	@sleep 3
	@echo "Catalog API available at http://localhost:8000 (via HAProxy)"
	@echo "Catalog UI available at http://localhost:8080 (via HAProxy)"

catalog-restart: ## Restart catalog services
	@echo "Restarting catalog services..."
	docker-compose restart catalog-api catalog-ui

scale-catalog-api: ## Scale Catalog API instances (usage: make scale-catalog-api N=3)
	@if [ -z "$(N)" ]; then \
		echo "Usage: make scale-catalog-api N=<number>"; \
		echo "Example: make scale-catalog-api N=3"; \
		exit 1; \
	fi
	@echo "Scaling Catalog API to $(N) instances..."
	docker-compose up -d --scale catalog-api=$(N) --no-recreate

scale-catalog-ui: ## Scale Catalog UI instances (usage: make scale-catalog-ui N=3)
	@if [ -z "$(N)" ]; then \
		echo "Usage: make scale-catalog-ui N=<number>"; \
		echo "Example: make scale-catalog-ui N=3"; \
		exit 1; \
	fi
	@echo "Scaling Catalog UI to $(N) instances..."
	docker-compose up -d --scale catalog-ui=$(N) --no-recreate

scale-catalog: ## Scale both Catalog API and UI (usage: make scale-catalog N=3)
	@if [ -z "$(N)" ]; then \
		echo "Usage: make scale-catalog N=<number>"; \
		echo "Example: make scale-catalog N=3"; \
		exit 1; \
	fi
	@echo "Scaling Catalog services to $(N) instances..."
	docker-compose up -d --scale catalog-api=$(N) --scale catalog-ui=$(N) --no-recreate
	@echo "View HAProxy stats: make ui-haproxy"

# ============================================================================
# Cleanup
# ============================================================================

clean: ## Clean up containers, volumes, and generated files
	@echo "Cleaning up..."
	docker-compose down -v
	rm -rf proto/*_pb2.py proto/*_pb2_grpc.py proto/__pycache__
	rm -rf venv
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

# ============================================================================
# Development Shortcuts
# ============================================================================

dev: setup proto-compile build up test ## Full development setup

quick-start: ## Quick start for first-time users
	@echo "==================================="
	@echo "Agent Platform - Quick Start"
	@echo "==================================="
	@echo ""
	@make setup
	@echo ""
	@make build
	@echo ""
	@make up
	@echo ""
	@echo "==================================="
	@echo "✓ Platform is ready!"
	@echo "==================================="
	@echo ""
	@echo "Next steps:"
	@echo "  1. Run tests:        make test"
	@echo "  2. View Consul UI:   make ui-consul"
	@echo "  3. View HAProxy UI:  make ui-haproxy"
	@echo "  4. Check services:   make consul-check"
	@echo "  5. Scale router:     make scale-router N=3"
	@echo "  6. View logs:        make logs"
	@echo "  7. Get help:         make help"
	@echo ""

# ============================================================================
# Aliases for backward compatibility
# ============================================================================

compile-proto: proto-compile ## Alias for proto-compile
consul-ui: ui-consul ## Alias for ui-consul
haproxy-ui: ui-haproxy ## Alias for ui-haproxy
check-consul: consul-check ## Alias for consul-check
cleanup-consul: consul-cleanup ## Alias for consul-cleanup
echo-logs: logs-echo ## Alias for logs-echo
weather-logs: logs-weather ## Alias for logs-weather
itinerary-logs: logs-itinerary ## Alias for logs-itinerary
router-logs: logs-router ## Alias for logs-router
haproxy-logs: logs-haproxy ## Alias for logs-haproxy
consul-logs: logs-consul ## Alias for logs-consul
