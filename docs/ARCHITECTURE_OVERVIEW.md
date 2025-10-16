# Architecture Documentation Overview

## Documentation Structure

The Agent Platform architecture is documented in three comprehensive, consistently-formatted documents:

### 1. [ARCHITECTURE.md](ARCHITECTURE.md) - Overall System
**Main architecture document covering the entire platform**

**Contents**:
- Complete system overview
- All major components (HAProxy, routers, services, Consul)
- Client layer (gRPC and MCP clients)
- Protocol gateways (MCP Server, direct gRPC)
- Communication flows for both protocols
- Scaling strategies
- Port allocation
- Performance characteristics
- Monitoring and observability

**When to read**: 
- First-time platform overview
- Understanding how all pieces fit together
- Planning deployment architecture
- Making scaling decisions

**Key Diagrams**:
- Complete system architecture (all layers)
- Port allocation table
- Service registry overview

---

### 2. [ARCHITECTURE_GRPC.md](ARCHITECTURE_GRPC.md) - gRPC Subsystem
**Deep dive into the gRPC-based internal communication**

**Contents**:
- gRPC router architecture and implementation
- Protocol Buffer definitions and services
- Service discovery via Consul
- HAProxy load balancing for gRPC
- Backend service patterns
- Client implementation examples
- Performance tuning
- Scaling gRPC components
- Troubleshooting gRPC issues

**When to read**:
- Building gRPC clients
- Implementing new agents/tools/workers
- Optimizing gRPC performance
- Debugging internal communication
- Understanding service discovery

**Key Diagrams**:
- gRPC client → backend flow
- Service discovery sequence
- Load balancing architecture

---

### 3. [ARCHITECTURE_MCP.md](ARCHITECTURE_MCP.md) - MCP Subsystem
**Deep dive into the Model Context Protocol integration**

**Contents**:
- MCP server architecture and implementation
- Protocol translation (MCP ↔ gRPC)
- Cursor IDE integration
- stdio and SSE transports
- Tool and resource mapping
- Scaling MCP servers
- HAProxy load balancing for MCP
- Troubleshooting MCP issues

**When to read**:
- Integrating with Cursor or other MCP clients
- Understanding protocol translation
- Debugging MCP connections
- Optimizing MCP performance
- Setting up AI IDE integrations

**Key Diagrams**:
- MCP client → backend flow
- Protocol translation layer
- MCP server architecture

---

## Quick Reference

### By Use Case

| What are you trying to do? | Read this document |
|-----------------------------|-------------------|
| Understand the whole platform | [ARCHITECTURE.md](ARCHITECTURE.md) |
| Browse available services | [CATALOG.md](CATALOG.md) - Web catalog UI |
| Build a Python gRPC client | [ARCHITECTURE_GRPC.md](ARCHITECTURE_GRPC.md) |
| Integrate Cursor IDE | [ARCHITECTURE_MCP.md](ARCHITECTURE_MCP.md) |
| Create a new agent | [ARCHITECTURE_GRPC.md](ARCHITECTURE_GRPC.md) |
| Scale the platform | [ARCHITECTURE.md](ARCHITECTURE.md) + [CATALOG.md](CATALOG.md) |
| Debug gRPC issues | [ARCHITECTURE_GRPC.md](ARCHITECTURE_GRPC.md) |
| Debug MCP issues | [ARCHITECTURE_MCP.md](ARCHITECTURE_MCP.md) |
| Deploy to production | All three documents |

### By Role

| Your Role | Start Here | Also Read |
|-----------|------------|-----------|
| **Platform Operator** | [ARCHITECTURE.md](ARCHITECTURE.md) | Both subsystem docs for troubleshooting |
| **Backend Developer** | [ARCHITECTURE_GRPC.md](ARCHITECTURE_GRPC.md) | [ARCHITECTURE.md](ARCHITECTURE.md) for context |
| **Frontend/IDE Developer** | [ARCHITECTURE_MCP.md](ARCHITECTURE_MCP.md) | [ARCHITECTURE.md](ARCHITECTURE.md) for context |
| **DevOps Engineer** | [ARCHITECTURE.md](ARCHITECTURE.md) | Both subsystem docs for specific issues |
| **New Team Member** | [ARCHITECTURE.md](ARCHITECTURE.md) first | Then subsystem docs as needed |

### By Component

| Component | Primary Document | Secondary Document |
|-----------|-----------------|-------------------|
| **HAProxy** | [ARCHITECTURE.md](ARCHITECTURE.md) | Specific subsystem doc for protocol details |
| **gRPC Router** | [ARCHITECTURE_GRPC.md](ARCHITECTURE_GRPC.md) | [ARCHITECTURE.md](ARCHITECTURE.md) for overall context |
| **MCP Server** | [ARCHITECTURE_MCP.md](ARCHITECTURE_MCP.md) | [ARCHITECTURE.md](ARCHITECTURE.md) for overall context |
| **Consul** | [ARCHITECTURE.md](ARCHITECTURE.md) | Both subsystem docs for service-specific details |
| **Agents** | [ARCHITECTURE_GRPC.md](ARCHITECTURE_GRPC.md) | [ARCHITECTURE.md](ARCHITECTURE.md) for deployment |
| **Tools** | [ARCHITECTURE_GRPC.md](ARCHITECTURE_GRPC.md) | [ARCHITECTURE_MCP.md](ARCHITECTURE_MCP.md) for MCP exposure |
| **Workers** | [ARCHITECTURE_GRPC.md](ARCHITECTURE_GRPC.md) | [ARCHITECTURE_MCP.md](ARCHITECTURE_MCP.md) for MCP exposure |

## Document Consistency

All three architecture documents follow the same structure:

1. **Overview** - What this subsystem does
2. **Architecture Diagram** - Visual representation using consistent box-and-arrow style
3. **Core Components** - Detailed component descriptions
4. **Data Flow Examples** - Step-by-step request flows
5. **Implementation Details** - Code examples and patterns
6. **Scaling Strategies** - How to scale this subsystem
7. **Monitoring** - How to observe and debug
8. **Troubleshooting** - Common issues and solutions
9. **Performance Characteristics** - Latency, throughput, resources
10. **Security Considerations** - Current state and production recommendations
11. **Related Documentation** - Links to other docs
12. **Summary** - Key takeaways

## Diagram Style

All diagrams use consistent ASCII art with:
- Clear layer separation with horizontal lines
- Vertical arrows (▼, ↓) for data flow
- Box drawing characters (┌─┐│└┘) for components
- Consistent indentation and alignment
- Labels for protocols and ports
- Annotations for key concepts

Example structure:
```
┌──────────────────────────────────────────┐
│              LAYER NAME                  │
├──────────────────────────────────────────┤
│                                          │
│  Component details                       │
│      ↓ Protocol/Port                    │
│                                          │
└──────────────────────────────────────────┘
```

## Reading Path

### For Comprehensive Understanding

1. **Start**: [ARCHITECTURE.md](ARCHITECTURE.md)
   - Get the big picture
   - Understand all components
   - See how protocols interact

2. **Then**: [ARCHITECTURE_GRPC.md](ARCHITECTURE_GRPC.md)
   - Deep dive into internal communication
   - Understand service discovery
   - Learn implementation patterns

3. **Finally**: [ARCHITECTURE_MCP.md](ARCHITECTURE_MCP.md)
   - Understand IDE integration
   - Learn protocol translation
   - See MCP-specific features

### For Quick Task Completion

1. **Identify your task** in the Quick Reference tables above
2. **Jump directly** to the relevant document
3. **Reference** [ARCHITECTURE.md](ARCHITECTURE.md) if you need broader context
4. **Cross-reference** the other subsystem doc if your task spans both protocols

## Additional Documentation

Beyond architecture, see also:

- **[QUICKSTART.md](QUICKSTART.md)** - Get started quickly
- **[README.md](../README.md)** - Project overview and usage
- **[SCALING_GUIDE.md](SCALING_GUIDE.md)** - Detailed scaling instructions
- **[LOAD_BALANCING.md](LOAD_BALANCING.md)** - HAProxy configuration details
- **[CURSOR_INTEGRATION.md](CURSOR_INTEGRATION.md)** - Complete Cursor setup guide
- **[MCP_CURSOR_SETUP.md](MCP_CURSOR_SETUP.md)** - Quick MCP reference
- **[MAKEFILE_REFERENCE.md](MAKEFILE_REFERENCE.md)** - All make commands

## Key Concepts

### Protocol Separation

The platform supports **two client protocols**:

1. **gRPC** - High-performance binary protocol for programmatic access
   - Direct access to backend services
   - Used by: Python clients, SDKs, automation scripts
   - Documented in: [ARCHITECTURE_GRPC.md](ARCHITECTURE_GRPC.md)

2. **MCP** - Model Context Protocol for AI IDE integration
   - JSON-RPC based, human-readable
   - Used by: Cursor IDE, Claude Desktop, MCP tools
   - Documented in: [ARCHITECTURE_MCP.md](ARCHITECTURE_MCP.md)

Both protocols access the **same backend services** but through different gateways.

### Naming Clarification

⚠️ **Important**: The "MCP Router" in the codebase is actually a **gRPC Router**:

| Current Name | What It Actually Is | Should Be Renamed To |
|--------------|-------------------|---------------------|
| `mcp-router` | gRPC request router | `grpc-router` |
| `mcp-server` | Model Context Protocol server | (correct name) ✅ |

The "MCP Router" is a legacy name from before MCP integration. It routes gRPC requests, not MCP requests. The "MCP Server" correctly implements the Model Context Protocol.

See [ARCHITECTURE_GRPC.md](ARCHITECTURE_GRPC.md) for details on the gRPC Router.  
See [ARCHITECTURE_MCP.md](ARCHITECTURE_MCP.md) for details on the MCP Server.

## Document Maintenance

When updating architecture:

1. **Update relevant document(s)**:
   - Component changes → update specific subsystem doc
   - Cross-cutting changes → update [ARCHITECTURE.md](ARCHITECTURE.md) and both subsystem docs

2. **Maintain consistency**:
   - Keep diagram styles consistent
   - Use same section structure
   - Cross-reference between docs

3. **Update this overview** if:
   - Adding new architecture documents
   - Changing document purposes
   - Reorganizing documentation structure

## Summary

Three comprehensive, consistently-formatted architecture documents:

📘 **[ARCHITECTURE.md](ARCHITECTURE.md)** - Overall system  
📗 **[ARCHITECTURE_GRPC.md](ARCHITECTURE_GRPC.md)** - gRPC subsystem  
📙 **[ARCHITECTURE_MCP.md](ARCHITECTURE_MCP.md)** - MCP subsystem  

Each document is:
- ✅ **Self-contained** - Can be read independently
- ✅ **Cross-referenced** - Links to related docs
- ✅ **Consistently formatted** - Same structure and diagram style
- ✅ **Comprehensive** - Covers all aspects of the subsystem
- ✅ **Practical** - Includes examples, code, and troubleshooting

**Start with [ARCHITECTURE.md](ARCHITECTURE.md), then dive into subsystems as needed!**

---

**Well-structured documentation for a well-structured platform** 📚

