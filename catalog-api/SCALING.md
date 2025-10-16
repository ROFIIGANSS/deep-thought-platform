# Catalog Services - Scaling & Architecture

## Overview

The catalog services (API and UI) are designed to scale horizontally and integrate with the existing Agent Platform infrastructure.

## Architecture

### 1. Consul Service Registration
Both catalog-api and catalog-ui register with Consul for service discovery:
- **catalog-api**: Registers with health checks on `/health`
- **catalog-ui**: Registers with health checks on `/health` (via nginx + Python sidecar)

### 2. HAProxy Load Balancing
All catalog services are accessed through HAProxy:
- **Catalog API**: `http://localhost:8000` → Routes to catalog-api backends
- **Catalog UI**: `http://localhost:8080` → Routes to catalog-ui backends

No direct port exposure - everything goes through HAProxy for:
- Load balancing
- Health checking
- Service discovery integration
- Consistent routing

### 3. Scaling Configuration
Both services start with **1 instance** and can scale up to **3 instances**:

```bash
# Scale both services to 3 instances
make scale-catalog N=3

# Scale API only
make scale-catalog-api N=3

# Scale UI only
make scale-catalog-ui N=3

# Scale down to 1 instance
make scale-catalog N=1
```

## Service Registration Details

### Catalog API
- **Language**: Python (FastAPI)
- **Registration**: Native Python Consul client
- **Health Check**: HTTP GET `/health`
- **Tags**: `catalog`, `api`, `http`
- **Port**: 8000

### Catalog UI
- **Stack**: React (Vite) + Nginx
- **Registration**: Python sidecar process
- **Health Check**: HTTP GET `/health`
- **Tags**: `catalog`, `ui`, `http`, `nginx`
- **Port**: 80

## HAProxy Configuration

### Frontends
```
catalog_api_frontend: Port 8000
catalog_ui_frontend: Port 8080
```

### Backends
```
catalog_api_backend:
  - Balance: roundrobin
  - Health Check: GET /health
  - Servers: catalog-api1, catalog-api2, catalog-api3

catalog_ui_backend:
  - Balance: roundrobin  
  - Health Check: GET /health
  - Servers: catalog-ui1, catalog-ui2, catalog-ui3
```

## Docker Compose Configuration

### Catalog API
```yaml
catalog-api:
  # No container_name - allows scaling
  # No direct port exposure - uses HAProxy
  deploy:
    replicas: 1  # Start with 1, scale to 3
  environment:
    - CONSUL_HOST=consul
    - CATALOG_API_PORT=8000
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
```

### Catalog UI
```yaml
catalog-ui:
  # No container_name - allows scaling
  # No direct port exposure - uses HAProxy
  deploy:
    replicas: 1  # Start with 1, scale to 3
  environment:
    - CONSUL_HOST=consul
    - CATALOG_UI_PORT=80
  healthcheck:
    test: ["CMD", "wget", "--no-verbose", "--tries=1", "--spider", "http://localhost:80/health"]
```

## Verification

### Check Consul Registration
```bash
# View all catalog-api instances
curl -s http://localhost:8500/v1/health/service/catalog-api | jq

# View all catalog-ui instances
curl -s http://localhost:8500/v1/health/service/catalog-ui | jq

# Or use the Makefile
make consul-check
```

### Check HAProxy Stats
```bash
# Open HAProxy dashboard
make ui-haproxy

# Visit http://localhost:8404
# Look for catalog_api_backend and catalog_ui_backend sections
```

### Test Load Balancing
```bash
# Multiple requests should hit different instances
for i in {1..10}; do
  curl -s http://localhost:8000/health
done
```

## Benefits

1. **High Availability**: Multiple instances provide redundancy
2. **Load Distribution**: HAProxy distributes traffic across instances
3. **Service Discovery**: Consul tracks all instances automatically
4. **Health Monitoring**: Unhealthy instances removed from rotation
5. **Zero Downtime**: Scale up/down without service interruption
6. **Centralized Routing**: All traffic through HAProxy
7. **Consistent Architecture**: Same pattern as other platform services

## Troubleshooting

### Service not in Consul
```bash
# Check container logs
docker logs agent-platform-server-catalog-api-1
docker logs agent-platform-server-catalog-ui-1

# Verify Consul connectivity
docker exec agent-platform-server-catalog-api-1 curl consul:8500/v1/status/leader
```

### HAProxy not routing
```bash
# Check HAProxy config
docker exec haproxy-lb cat /usr/local/etc/haproxy/haproxy.cfg

# View HAProxy logs
docker logs haproxy-lb

# Restart HAProxy
docker-compose restart haproxy
```

### Health checks failing
```bash
# Test health endpoint directly
docker exec agent-platform-server-catalog-api-1 curl localhost:8000/health
docker exec agent-platform-server-catalog-ui-1 wget -O- localhost:80/health
```

## Performance Considerations

- **API**: Each instance can handle ~1000 req/s
- **UI**: Nginx can serve ~10000 req/s per instance
- **Recommended**: 2-3 instances for production
- **Maximum**: 10 instances (HAProxy configured for up to 10)

## Future Enhancements

1. Auto-scaling based on metrics
2. Circuit breaker patterns
3. Rate limiting per instance
4. Metrics collection (Prometheus)
5. Distributed tracing
6. Cache layer (Redis)

