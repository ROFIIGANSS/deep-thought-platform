# Makefile Quick Reference

This document provides a quick reference for all available `make` targets in the Agent Platform.

## Naming Conventions

All targets follow consistent naming patterns:

- **General actions**: `<action>` (e.g., `build`, `up`, `down`)
- **Protocol operations**: `proto-<action>` (e.g., `proto-compile`)
- **Service logs**: `logs-<service>` (e.g., `logs-router`, `logs-echo`)
- **User interfaces**: `ui-<service>` (e.g., `ui-consul`, `ui-haproxy`)
- **Scaling operations**: `scale-<service>` (e.g., `scale-router`, `scale-echo`)
- **Consul operations**: `consul-<action>` (e.g., `consul-check`, `consul-cleanup`)

## Quick Start

```bash
make help           # Show all available commands
make quick-start    # Complete setup for first-time users
make dev            # Full development setup
```

## Setup & Build

```bash
make setup          # Run initial setup (venv, deps, proto compilation)
make proto-compile  # Compile Protocol Buffer definitions
make build          # Build all Docker images
make rebuild        # Rebuild and restart all services
```

## Service Management

```bash
make up             # Start all services
make down           # Stop all services
make restart        # Restart all services
make status         # Show status of all services
```

## Logs

```bash
make logs               # Show logs from all services (streaming)
make logs-router        # Show MCP Router logs
make logs-consul        # Show Consul logs
make logs-haproxy       # Show HAProxy logs
make logs-echo          # Show Echo Agent logs
make logs-weather       # Show Weather Tool logs
make logs-itinerary     # Show Itinerary Worker logs
```

## User Interfaces

```bash
make ui-consul      # Open Consul UI at http://localhost:8500
make ui-haproxy     # Open HAProxy stats at http://localhost:8404
```

## Service Discovery

Query available agents, tools, and workers:

```bash
make mcp-query              # Query all services (agents, tools, workers)
make mcp-query-agents       # Query available agents
make mcp-query-tools        # Query available tools  
make mcp-query-workers      # Query available workers
make mcp-query-json         # Query all and output as JSON
```

## Testing

```bash
make test           # Run test client through MCP Router
```

## Scaling

```bash
# Scale specific services
make scale-router N=3       # Scale MCP Router to 3 instances
make scale-echo N=2         # Scale Echo Agent to 2 instances
make scale-weather N=2      # Scale Weather Tool to 2 instances
make scale-itinerary N=2    # Scale Itinerary Worker to 2 instances

# Scale all services at once
make scale-all N=3          # Scale all services to 3 instances

# Scale down
make scale-down             # Scale all services back to 1 instance
```

## Consul Operations

```bash
make consul-check       # Check services registered in Consul
make consul-cleanup     # Clean up stale service registrations
make consul-purge       # Purge ALL Consul data (destructive!)
```

## Cleanup

```bash
make clean          # Clean up containers, volumes, and generated files
```

## Backward Compatibility Aliases

For convenience, old command names are aliased to new ones:

```bash
# Old Command          →  New Command
make compile-proto    →  make proto-compile
make consul-ui        →  make ui-consul
make haproxy-ui       →  make ui-haproxy
make check-consul     →  make consul-check
make cleanup-consul   →  make consul-cleanup
make echo-logs        →  make logs-echo
make router-logs      →  make logs-router
# ... and so on
```

## Common Workflows

### First Time Setup

```bash
make quick-start    # Does: setup → build → up → status
```

### Daily Development

```bash
make up             # Start services
make test           # Run tests
make logs-router    # View router logs
make down           # Stop when done
```

### Scaling Demo

```bash
make scale-router N=5       # Scale router to 5 instances
make ui-haproxy             # View load balancer stats
make consul-check           # View service registry
make scale-down             # Reset to 1 instance
```

### Troubleshooting

```bash
make status                 # Check service status
make consul-check           # Check service registration
make logs-router            # View router logs
make consul-cleanup         # Clean up stale registrations
make rebuild                # Full rebuild if needed
```

### Complete Reset

```bash
make clean                  # Remove everything
make setup                  # Re-setup
make build                  # Rebuild images
make up                     # Start fresh
```

## Environment Variables

Some commands accept environment variables:

```bash
N=5 make scale-router       # Scale to 5 instances
```

## Tips

1. **Use tab completion**: Bash/Zsh can auto-complete make targets
2. **Check help anytime**: `make help` shows all available commands
3. **Logs are streaming**: Press `Ctrl+C` to exit log streaming
4. **Aliases work too**: Both old and new command names work
5. **Services auto-register**: Consul discovery happens automatically

## Command Groups

### Core Operations
`setup`, `build`, `up`, `down`, `restart`, `status`, `clean`

### Monitoring
`logs-*`, `ui-*`, `consul-check`, `status`

### Scaling
`scale-*`, `scale-all`, `scale-down`

### Development
`dev`, `quick-start`, `test`, `rebuild`

### Maintenance
`consul-cleanup`, `consul-purge`, `proto-compile`

---

**Pro Tip**: Type `make` (with tab) and press Tab twice to see all available targets!

