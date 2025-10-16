# Agent Platform - Scaling Guide

## Overview

The Agent Platform supports horizontal scaling of all services including the **MCP Router** (with HAProxy load balancing), agents, tools, and workers. Each instance automatically registers with Consul for service discovery, enabling load balancing and high availability.

## 🆕 MCP Router Load Balancing

The MCP Router now includes **HAProxy load balancing** and can be scaled horizontally:

### Quick Start
```bash
# Scale MCP Router to 3 instances
docker-compose up -d --scale mcp-router=3

# Use the management script
./scripts/manage_routers.sh scale 3
```

### Monitoring
- **HAProxy Stats**: http://localhost:8404
- **Consul Registry**: http://localhost:8500/ui/dc1/services/mcp-router

**📘 For comprehensive load balancing documentation, see [LOAD_BALANCING.md](LOAD_BALANCING.md)**

## Key Concepts

### Service Discovery with Consul
- Each service instance gets a **unique service ID** (e.g., `echo-agent-abc123`)
- All instances share the same **service name** (e.g., `agent-echo`)
- Consul tracks all instances and their health status
- The MCP Router can discover and load balance across all healthy instances

### Dynamic Port Allocation
- Container ports remain fixed (e.g., 50052 for echo-agent)
- Host ports are dynamically assigned by Docker
- Services communicate via the Docker network using container hostnames

## Scaling Commands

### Quick Scaling via Makefile

#### Scale Individual Services
```bash
# Scale Echo Agent to 3 instances
make scale-echo N=3

# Scale Weather Tool to 5 instances
make scale-weather N=5

# Scale Itinerary Worker to 2 instances
make scale-itinerary N=2
```

#### Scale All Services
```bash
# Scale all services to 3 instances
make scale-all N=3
```

#### Scale Down to Default
```bash
# Scale all services back to 1 instance
make scale-down
```

### Direct Docker Compose Commands

```bash
# Scale specific service
docker-compose up -d --scale echo-agent=3 --no-recreate

# Scale multiple services at once
docker-compose up -d --scale echo-agent=3 --scale weather-tool=2 --no-recreate

# Scale down
docker-compose up -d --scale echo-agent=1 --no-recreate
```

## Monitoring Scaled Services

### Check Container Status
```bash
# View all containers
docker-compose ps

# View specific service
docker-compose ps echo-agent
```

### Check Consul Registration
```bash
# Use the built-in Makefile target
make check-consul

# Or query Consul API directly
curl http://localhost:8500/v1/health/service/agent-echo | jq
curl http://localhost:8500/v1/health/service/tool-weather | jq
curl http://localhost:8500/v1/health/service/worker-itinerary | jq
```

### View Logs
```bash
# View logs from all instances of a service
docker-compose logs -f echo-agent

# View logs from a specific container
docker logs agent-platform-server-echo-agent-1
```

### Consul UI
Access the Consul UI at: http://localhost:8500

Navigate to **Services** to see:
- All registered service instances
- Health check status
- Service metadata
- Instance addresses and ports

## Architecture Benefits

### 1. **High Availability**
- If one instance fails, others continue serving requests
- Health checks automatically remove unhealthy instances

### 2. **Load Distribution**
- Multiple instances can handle requests in parallel
- Consul enables round-robin or other load balancing strategies

### 3. **Easy Scaling**
- Scale up during high load periods
- Scale down to save resources
- No code changes required

### 4. **Zero Downtime Deployment**
- Scale up new instances with updated code
- Remove old instances after new ones are healthy
- Gradual rollout capabilities

## Best Practices

### 1. **Monitor Resource Usage**
```bash
# Check CPU and memory usage
docker stats

# Check specific service
docker stats agent-platform-server-echo-agent-1
```

### 2. **Scale Based on Load**
- Start with 1 instance for development
- Scale to 2-3 instances for production
- Use metrics to determine optimal count

### 3. **Health Checks**
- Services automatically register TCP health checks with Consul
- Consul checks connectivity every 10 seconds
- Failed instances are automatically deregistered

### 4. **Graceful Shutdown**
```bash
# Scale down gradually
make scale-echo N=2
# Wait for requests to drain
sleep 30
make scale-echo N=1
```

## Example Scaling Workflow

### Development
```bash
# Single instance of each service
docker-compose up -d
```

### Testing with Load
```bash
# Scale up for load testing
make scale-all N=3

# Run your tests
make test

# Check Consul to verify all instances are healthy
make check-consul
```

### Production Deployment
```bash
# Start with production scale
make scale-all N=3

# Monitor services
make check-consul
docker-compose ps

# View logs from all instances
make logs
```

### Scaling Individual Services Based on Usage
```bash
# If Echo Agent is heavily used
make scale-echo N=5

# If Weather Tool has light load
make scale-weather N=2

# Check status
make check-consul
```

## Troubleshooting

### Services Not Scaling
**Problem**: Container name conflicts  
**Solution**: Remove `container_name` from docker-compose.yml (already done)

### Port Conflicts
**Problem**: Port already in use  
**Solution**: Use dynamic port allocation (already configured)

### Consul Registration Issues
**Problem**: Services not appearing in Consul  
**Check**:
```bash
# Verify Consul is healthy
docker-compose ps consul

# Check service logs
docker-compose logs echo-agent
```

### Old Registrations in Consul
**Problem**: Stale service registrations  
**Solution**:
```bash
# Restart Consul to clear registrations
docker-compose restart consul

# Or manually deregister via API
curl -X PUT http://localhost:8500/v1/agent/service/deregister/old-service-id
```

## Advanced Configuration

### Custom Health Checks
Edit the service code to add HTTP health check endpoints:
```python
# In your service's serve() function
consul_client.agent.service.register(
    name='agent-echo',
    service_id=service_id,
    address=hostname,
    port=int(port),
    check=consul.Check.http(f'http://{hostname}:{port}/health', interval='10s')
)
```

### Load Balancing Strategies
Configure Consul with different load balancing:
- Round Robin (default)
- Least Connections
- Random
- Weighted

### Auto-scaling
Implement auto-scaling with:
- Docker Swarm mode
- Kubernetes
- Custom monitoring + scaling scripts

## Summary

The Agent Platform is now fully scalable! Key points:

✅ **Easy scaling** with `make scale-echo N=3` commands  
✅ **Automatic service discovery** via Consul  
✅ **Health monitoring** and automatic failover  
✅ **Dynamic port allocation** to avoid conflicts  
✅ **Zero-code changes** required for scaling  
✅ **Production-ready** architecture  

For questions or issues, check the logs or Consul UI for detailed information.

