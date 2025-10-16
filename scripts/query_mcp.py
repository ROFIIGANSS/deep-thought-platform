#!/usr/bin/env python3
"""
MCP Service Discovery Query Tool
Queries the MCP Router for available agents, tools, and workers
"""

import grpc
import sys
import os
import argparse
import json

# Add proto to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'proto'))

try:
    import agent_platform_pb2
    import agent_platform_pb2_grpc
except ImportError:
    print("Error: Proto files not compiled. Run: make proto-compile")
    sys.exit(1)


def query_agents(host='localhost', port=50051, output_json=False):
    """Query available agents"""
    try:
        channel = grpc.insecure_channel(f'{host}:{port}')
        stub = agent_platform_pb2_grpc.AgentServiceStub(channel)
        
        request = agent_platform_pb2.ListAgentsRequest()
        response = stub.ListAgents(request)
        
        channel.close()
        
        if output_json:
            agents_data = []
            for agent in response.agents:
                agents_data.append({
                    'agent_id': agent.agent_id,
                    'name': agent.name,
                    'description': agent.description,
                    'capabilities': list(agent.capabilities),
                    'endpoint': agent.endpoint
                })
            return agents_data
        else:
            return response.agents
            
    except Exception as e:
        print(f"Error querying agents: {e}", file=sys.stderr)
        return [] if output_json else None


def query_tools(host='localhost', port=50051, output_json=False):
    """Query available tools"""
    try:
        channel = grpc.insecure_channel(f'{host}:{port}')
        stub = agent_platform_pb2_grpc.ToolServiceStub(channel)
        
        request = agent_platform_pb2.ListToolsRequest()
        response = stub.ListTools(request)
        
        channel.close()
        
        if output_json:
            tools_data = []
            for tool in response.tools:
                params = []
                for param in tool.parameters:
                    params.append({
                        'name': param.name,
                        'type': param.type,
                        'required': param.required,
                        'description': param.description
                    })
                tools_data.append({
                    'tool_id': tool.tool_id,
                    'name': tool.name,
                    'description': tool.description,
                    'endpoint': tool.endpoint,
                    'parameters': params
                })
            return tools_data
        else:
            return response.tools
            
    except Exception as e:
        print(f"Error querying tools: {e}", file=sys.stderr)
        return [] if output_json else None


def query_workers(host='localhost', port=50051, output_json=False):
    """Query available workers"""
    try:
        channel = grpc.insecure_channel(f'{host}:{port}')
        stub = agent_platform_pb2_grpc.TaskWorkerStub(channel)
        
        request = agent_platform_pb2.ListWorkersRequest()
        response = stub.ListWorkers(request)
        
        channel.close()
        
        if output_json:
            workers_data = []
            for worker in response.workers:
                workers_data.append({
                    'worker_id': worker.worker_id,
                    'name': worker.name,
                    'description': worker.description,
                    'endpoint': worker.endpoint,
                    'tags': list(worker.tags)
                })
            return workers_data
        else:
            return response.workers
            
    except Exception as e:
        print(f"Error querying workers: {e}", file=sys.stderr)
        return [] if output_json else None


def print_agents(agents):
    """Print agents in human-readable format"""
    if not agents:
        print("No agents found")
        return
    
    print("\n" + "="*70)
    print("AGENTS")
    print("="*70)
    
    for agent in agents:
        print(f"\n📦 {agent.name}")
        print(f"   ID: {agent.agent_id}")
        print(f"   Description: {agent.description}")
        print(f"   Endpoint: {agent.endpoint}")
        if agent.capabilities:
            print(f"   Capabilities: {', '.join(agent.capabilities)}")


def print_tools(tools):
    """Print tools in human-readable format"""
    if not tools:
        print("No tools found")
        return
    
    print("\n" + "="*70)
    print("TOOLS")
    print("="*70)
    
    for tool in tools:
        print(f"\n🛠️  {tool.name}")
        print(f"   ID: {tool.tool_id}")
        print(f"   Description: {tool.description}")
        print(f"   Endpoint: {tool.endpoint}")
        if tool.parameters:
            print(f"   Parameters:")
            for param in tool.parameters:
                required = "required" if param.required else "optional"
                print(f"      - {param.name} ({param.type}, {required}): {param.description}")


def print_workers(workers):
    """Print workers in human-readable format"""
    if not workers:
        print("No workers found")
        return
    
    print("\n" + "="*70)
    print("WORKERS")
    print("="*70)
    
    for worker in workers:
        print(f"\n⚙️  {worker.name}")
        print(f"   ID: {worker.worker_id}")
        print(f"   Description: {worker.description}")
        print(f"   Endpoint: {worker.endpoint}")
        if worker.tags:
            print(f"   Tags: {', '.join(worker.tags)}")


def main():
    parser = argparse.ArgumentParser(
        description='Query MCP Router for available services',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s agents           # List all agents
  %(prog)s tools            # List all tools
  %(prog)s workers          # List all workers
  %(prog)s all              # List everything
  %(prog)s all --json       # Output as JSON
  %(prog)s agents --host localhost --port 50051
        """
    )
    
    parser.add_argument(
        'service_type',
        choices=['agents', 'tools', 'workers', 'all'],
        help='Type of service to query'
    )
    parser.add_argument(
        '--host',
        default='localhost',
        help='MCP Router host (default: localhost)'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=50051,
        help='MCP Router port (default: 50051)'
    )
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output as JSON'
    )
    
    args = parser.parse_args()
    
    print(f"Querying MCP Router at {args.host}:{args.port}...")
    
    result = {}
    
    if args.service_type in ['agents', 'all']:
        agents = query_agents(args.host, args.port, args.json)
        if args.json:
            result['agents'] = agents
        else:
            print_agents(agents)
    
    if args.service_type in ['tools', 'all']:
        tools = query_tools(args.host, args.port, args.json)
        if args.json:
            result['tools'] = tools
        else:
            print_tools(tools)
    
    if args.service_type in ['workers', 'all']:
        workers = query_workers(args.host, args.port, args.json)
        if args.json:
            result['workers'] = workers
        else:
            print_workers(workers)
    
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print("\n" + "="*70)
        print("✓ Query complete")
        print("="*70 + "\n")


if __name__ == '__main__':
    main()

