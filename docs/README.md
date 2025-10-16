# Agent Platform Documentation

Complete documentation for the Agent Platform - a distributed microservices architecture for running autonomous agents and tools.

## 📚 Documentation Structure

### 🚀 Getting Started

| Document | Description |
|----------|-------------|
| [START_HERE.md](START_HERE.md) | **Start here!** New user welcome guide and orientation |
| [QUICKSTART.md](QUICKSTART.md) | 5-minute quick start to get the platform running |

### 🏗️ Architecture

| Document | Description |
|----------|-------------|
| [ARCHITECTURE.md](ARCHITECTURE.md) | **Overall system architecture** - dual-protocol (gRPC + MCP) platform |
| [ARCHITECTURE_GRPC.md](ARCHITECTURE_GRPC.md) | **gRPC subsystem** - detailed gRPC router and service architecture |
| [ARCHITECTURE_MCP.md](ARCHITECTURE_MCP.md) | **MCP subsystem** - Model Context Protocol integration for Cursor IDE |
| [ARCHITECTURE_OVERVIEW.md](ARCHITECTURE_OVERVIEW.md) | **Navigation guide** - how to use the architecture documentation |

**💡 Reading Path:**
1. Start with `ARCHITECTURE.md` for the big picture
2. Dive into `ARCHITECTURE_GRPC.md` or `ARCHITECTURE_MCP.md` as needed
3. Use `ARCHITECTURE_OVERVIEW.md` for quick lookups

### 🔌 Integration

| Document | Description |
|----------|-------------|
| [CURSOR_INTEGRATION.md](CURSOR_INTEGRATION.md) | **Complete Cursor IDE integration guide** - SSE, stdio, troubleshooting |
| [MCP_CURSOR_SETUP.md](MCP_CURSOR_SETUP.md) | **Quick MCP reference** - fast setup for Cursor |
| [CURSOR_STATUS_GUIDE.md](CURSOR_STATUS_GUIDE.md) | Understanding Cursor connection status indicators |

### 📈 Scaling & Operations

| Document | Description |
|----------|-------------|
| [SCALING_GUIDE.md](SCALING_GUIDE.md) | **Comprehensive scaling guide** - horizontal scaling strategies |
| [SCALING_DEMO.md](SCALING_DEMO.md) | **Live demo** - step-by-step scaling demonstration |
| [LOAD_BALANCING.md](LOAD_BALANCING.md) | **HAProxy configuration** - load balancing details |
| [QUICK_REFERENCE_LOAD_BALANCING.md](QUICK_REFERENCE_LOAD_BALANCING.md) | Quick command reference for load balancing |

### 🛠️ Features & Guides

| Document | Description |
|----------|-------------|
| [CATALOG.md](CATALOG.md) | **Web-based service catalog** - live discovery and documentation |
| [HEALTH_RESILIENCE.md](HEALTH_RESILIENCE.md) | **🆕 v1.1.0** Health-aware service consolidation |
| [DEDUPLICATION_GUIDE.md](DEDUPLICATION_GUIDE.md) | **🆕 v1.1.0** Automatic service deduplication |
| [SESSION_ID_GUIDE.md](SESSION_ID_GUIDE.md) | **🆕 v1.1.0** Session ID for context recovery |
| [ECHO_AGENT_USAGE.md](ECHO_AGENT_USAGE.md) | How to use the Echo Agent |
| [AGENTS_AS_TOOLS.md](AGENTS_AS_TOOLS.md) | Using agents as MCP tools in Cursor |
| [MCP_SERVICE_DISCOVERY.md](MCP_SERVICE_DISCOVERY.md) | Service discovery and querying guide |
| [MCP_HAPROXY_ARCHITECTURE.md](MCP_HAPROXY_ARCHITECTURE.md) | MCP Server HAProxy integration |
| [SSE_IMPLEMENTATION.md](SSE_IMPLEMENTATION.md) | Server-Sent Events implementation details |
| [MAKEFILE_REFERENCE.md](MAKEFILE_REFERENCE.md) | **All make commands** - complete reference |

## 🎯 Documentation by Use Case

### I want to...

**Get started quickly**
→ [QUICKSTART.md](QUICKSTART.md)

**Understand the architecture**
→ [ARCHITECTURE.md](ARCHITECTURE.md) → [ARCHITECTURE_OVERVIEW.md](ARCHITECTURE_OVERVIEW.md)

**Build a gRPC client**
→ [ARCHITECTURE_GRPC.md](ARCHITECTURE_GRPC.md)

**Integrate with Cursor IDE**
→ [CURSOR_INTEGRATION.md](CURSOR_INTEGRATION.md)

**Scale the platform**
→ [SCALING_GUIDE.md](SCALING_GUIDE.md)

**Use session IDs for context** 🆕
→ [SESSION_ID_GUIDE.md](SESSION_ID_GUIDE.md)

**Monitor service health** 🆕
→ [HEALTH_RESILIENCE.md](HEALTH_RESILIENCE.md)

**Understand deduplication** 🆕
→ [DEDUPLICATION_GUIDE.md](DEDUPLICATION_GUIDE.md)

**Browse service catalog** 🆕
→ [CATALOG.md](CATALOG.md) or visit http://localhost:8080

**Use the Echo Agent**
→ [ECHO_AGENT_USAGE.md](ECHO_AGENT_USAGE.md)

**Find make commands**
→ [MAKEFILE_REFERENCE.md](MAKEFILE_REFERENCE.md)

**Understand service discovery**
→ [MCP_SERVICE_DISCOVERY.md](MCP_SERVICE_DISCOVERY.md)

**Configure load balancing**
→ [LOAD_BALANCING.md](LOAD_BALANCING.md)

**Debug MCP/Cursor issues**
→ [ARCHITECTURE_MCP.md](ARCHITECTURE_MCP.md) → [CURSOR_INTEGRATION.md](CURSOR_INTEGRATION.md)

## 📖 Documentation by Role

### New User
1. [START_HERE.md](START_HERE.md) - Welcome!
2. [QUICKSTART.md](QUICKSTART.md) - Get it running
3. [ARCHITECTURE.md](ARCHITECTURE.md) - Understand the system

### Developer
1. [ARCHITECTURE_GRPC.md](ARCHITECTURE_GRPC.md) - gRPC development
2. [ECHO_AGENT_USAGE.md](ECHO_AGENT_USAGE.md) - Agent examples
3. [MAKEFILE_REFERENCE.md](MAKEFILE_REFERENCE.md) - Commands

### Cursor User
1. [CURSOR_INTEGRATION.md](CURSOR_INTEGRATION.md) - Setup guide
2. [MCP_CURSOR_SETUP.md](MCP_CURSOR_SETUP.md) - Quick reference
3. [ARCHITECTURE_MCP.md](ARCHITECTURE_MCP.md) - Deep dive

### DevOps / Operator
1. [SCALING_GUIDE.md](SCALING_GUIDE.md) - Scaling strategies
2. [LOAD_BALANCING.md](LOAD_BALANCING.md) - HAProxy config
3. [ARCHITECTURE.md](ARCHITECTURE.md) - System overview

## 🔍 Quick Reference

### Essential Commands

```bash
# Start the platform
make up

# Check status
make status

# View documentation
ls docs/

# Scale services
make scale-router N=3
make scale-all N=3

# Query services
make mcp-query

# View logs
make logs

# Open UIs
make ui-consul    # http://localhost:8500
make ui-haproxy   # http://localhost:8404
```

### Key Ports

| Port | Service | Access |
|------|---------|--------|
| 50051 | gRPC Router (via HAProxy) | Public |
| 3000 | MCP Server (via HAProxy) | Public |
| 8404 | HAProxy Stats | Public |
| 8500 | Consul UI | Public |
| 50052 | Echo Agent | Internal |
| 50053 | Weather Tool | Internal |
| 50054 | Itinerary Worker | Internal |

## 📚 Document Categories

### Core Documentation (Read First)
- ✅ START_HERE.md
- ✅ QUICKSTART.md
- ✅ ARCHITECTURE.md

### Architecture Documentation
- ✅ ARCHITECTURE_GRPC.md
- ✅ ARCHITECTURE_MCP.md
- ✅ ARCHITECTURE_OVERVIEW.md

### Integration Documentation
- ✅ CURSOR_INTEGRATION.md
- ✅ MCP_CURSOR_SETUP.md
- ✅ CURSOR_STATUS_GUIDE.md

### Operational Documentation
- ✅ SCALING_GUIDE.md
- ✅ LOAD_BALANCING.md
- ✅ SCALING_DEMO.md

### Feature Documentation
- ✅ CATALOG.md
- 🆕 HEALTH_RESILIENCE.md (v1.1.0)
- 🆕 DEDUPLICATION_GUIDE.md (v1.1.0)
- 🆕 SESSION_ID_GUIDE.md (v1.1.0)
- ✅ ECHO_AGENT_USAGE.md
- ✅ AGENTS_AS_TOOLS.md
- ✅ MCP_SERVICE_DISCOVERY.md
- ✅ MCP_HAPROXY_ARCHITECTURE.md
- ✅ SSE_IMPLEMENTATION.md

### Reference Documentation
- ✅ MAKEFILE_REFERENCE.md
- ✅ QUICK_REFERENCE_LOAD_BALANCING.md

## 🆘 Need Help?

**Getting Started Issues:**
→ Check [QUICKSTART.md](QUICKSTART.md) troubleshooting section

**Architecture Questions:**
→ Start with [ARCHITECTURE_OVERVIEW.md](ARCHITECTURE_OVERVIEW.md)

**Cursor Not Working:**
→ Follow [CURSOR_INTEGRATION.md](CURSOR_INTEGRATION.md) troubleshooting

**Scaling Issues:**
→ See [SCALING_GUIDE.md](SCALING_GUIDE.md) troubleshooting

**Service Discovery:**
→ Run `make consul-check` and see [MCP_SERVICE_DISCOVERY.md](MCP_SERVICE_DISCOVERY.md)

## 📝 Documentation Standards

All documentation follows these principles:
- ✅ **Practical** - includes working examples
- ✅ **Complete** - covers the topic thoroughly
- ✅ **Structured** - consistent organization
- ✅ **Cross-referenced** - links to related docs
- ✅ **Up-to-date** - reflects current implementation

## 🔗 External Resources

- [gRPC Documentation](https://grpc.io/docs/)
- [Protocol Buffers](https://developers.google.com/protocol-buffers)
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [Consul Documentation](https://www.consul.io/docs)
- [HAProxy Documentation](http://www.haproxy.org/)
- [Docker Documentation](https://docs.docker.com/)

---

**📚 Well-documented platform for well-architected systems**

[← Back to Main README](../README.md)

