# MCP Router Load Balancing - Quick Reference

## 🚀 Quick Commands

### Scale Router Instances

```bash
# Scale to 3 instances
docker-compose up -d --scale mcp-router=3

# Scale to 5 instances
docker-compose up -d --scale mcp-router=5

# Using Makefile
make scale-router N=3

# Using management script
./scripts/manage_routers.sh scale 3
```

### Monitor & Check Status

```bash
# Show router status
./scripts/manage_routers.sh status

# Check health
./scripts/manage_routers.sh health

# Open HAProxy stats dashboard
./scripts/manage_routers.sh haproxy
# OR
make haproxy-ui
# OR visit: http://localhost:8404

# Open Consul UI
./scripts/manage_routers.sh consul
# OR
make consul-ui
# OR visit: http://localhost:8500/ui/dc1/services/mcp-router
```

### View Logs

```bash
# All router logs
./scripts/manage_routers.sh logs

# Specific logs
make router-logs      # MCP Router
make haproxy-logs     # HAProxy
make consul-logs      # Consul
```

### Management Script

```bash
./scripts/manage_routers.sh <command>

Commands:
  scale <n>      Scale to N router instances
  status         Show status of all instances
  health         Check health of all services
  haproxy        Open HAProxy stats dashboard
  consul         Open Consul UI
  logs           Tail logs from all routers
  restart        Restart all router instances
  help           Show help message
```

## 📊 Monitoring URLs

| Service | URL | Description |
|---------|-----|-------------|
| **HAProxy Stats** | http://localhost:8404 | Load balancer statistics & health |
| **Consul UI** | http://localhost:8500 | Service registry & health checks |
| **MCP Router** | localhost:50051 | gRPC endpoint (load balanced) |

## 🔍 Health Checks

### Quick Health Check

```bash
# Check all services
./scripts/manage_routers.sh health

# OR check individual components
curl http://localhost:8500/v1/health/service/mcp-router?passing=true | jq
curl http://localhost:8404/stats
```

### Verify Load Balancing

```bash
# 1. Scale to multiple instances
docker-compose up -d --scale mcp-router=3

# 2. Check instances in Consul
curl -s http://localhost:8500/v1/health/service/mcp-router?passing=true | \
  jq -r '.[] | "\(.Service.ID) - \(.Service.Address):\(.Service.Port)"'

# 3. View HAProxy backend status
curl http://localhost:8404/stats | grep mcp-router
```

## 🎯 Common Scenarios

### Scale Up for High Load

```bash
# Increase to 5 instances
make scale-router N=5

# Verify all are healthy
./scripts/manage_routers.sh status

# Monitor distribution
open http://localhost:8404
```

### Scale Down

```bash
# Reduce to 2 instances
make scale-router N=2

# Scale all services down
make scale-down
```

### Troubleshooting Unhealthy Instance

```bash
# 1. Check which instances are unhealthy
./scripts/manage_routers.sh health

# 2. View logs for errors
make router-logs

# 3. Restart all routers
./scripts/manage_routers.sh restart

# 4. Check HAProxy status
open http://localhost:8404
```

### Test Failover

```bash
# 1. Start with 3 instances
make scale-router N=3

# 2. Note instance IDs
docker ps | grep mcp-router

# 3. Kill one instance
docker stop agent-platform-server-mcp-router-1

# 4. Verify HAProxy removes it
# Visit: http://localhost:8404

# 5. Requests still work (distributed to healthy instances)
python scripts/test_client.py
```

## 📈 Recommended Configurations

### Development
```bash
docker-compose up -d --scale mcp-router=1
```
- 1 instance
- Minimal resources
- Easy debugging

### Testing/Staging
```bash
docker-compose up -d --scale mcp-router=2
```
- 2 instances
- Test load balancing
- Verify failover

### Production
```bash
docker-compose up -d --scale mcp-router=5
```
- 3-5+ instances
- High availability
- Better throughput
- Scale based on metrics

## 🔧 Configuration Files

| File | Purpose |
|------|---------|
| `docker-compose.yml` | Service definitions, HAProxy, Router config |
| `haproxy/haproxy.cfg` | Load balancer configuration |
| `mcp-router/app.py` | Router implementation with Consul registration |
| `scripts/manage_routers.sh` | Management utility |

## 📚 Full Documentation

- **[LOAD_BALANCING.md](LOAD_BALANCING.md)** - Complete guide with advanced features
- **[SCALING_GUIDE.md](SCALING_GUIDE.md)** - General scaling documentation
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - System architecture overview
- **[SCALING_DEMO.md](SCALING_DEMO.md)** - Live scaling demonstration

## 💡 Tips

1. **Start small**: Begin with 2-3 instances, scale based on load
2. **Monitor actively**: Use HAProxy stats and Consul UI regularly
3. **Test failover**: Verify system works when instances fail
4. **Check logs**: Use `./scripts/manage_routers.sh logs` for issues
5. **Use Makefile**: Convenient targets for common operations

## ⚠️ Important Notes

- **Port 50051**: Public-facing port (HAProxy)
- **Port 8404**: HAProxy statistics (public)
- **Port 8500**: Consul UI (public)
- Router instances use **dynamic host ports**
- All instances register in **Consul** automatically
- HAProxy does **health checks** every 2 seconds
- Each router has a **unique service ID**

## 🐛 Troubleshooting Quick Reference

| Issue | Solution |
|-------|----------|
| Router won't scale | Check no `container_name` in docker-compose.yml |
| HAProxy not routing | Verify Consul DNS: `docker exec haproxy-lb nslookup mcp-router consul` |
| Instance not in Consul | Check logs: `make router-logs` |
| All instances DOWN | Check network connectivity, restart services |
| High latency | Scale up: `make scale-router N=5` |

---

**Quick Help**: `./scripts/manage_routers.sh help`  
**Emergency**: `docker-compose restart` or `make restart`

