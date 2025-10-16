#!/usr/bin/env python3
"""
Test client for the Agent Platform
Tests connectivity and basic functionality through the MCP Router
"""

import grpc
import sys
import os
import uuid

# Add proto to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'proto'))

try:
    import agent_platform_pb2
    import agent_platform_pb2_grpc
except ImportError:
    print("Error: Proto files not compiled. Run scripts/compile_proto.sh first")
    sys.exit(1)


def test_echo_agent(host='localhost', port=50051):
    """Test the Echo Agent through MCP Router"""
    print(f"\n=== Testing Echo Agent through MCP Router at {host}:{port} ===")
    
    try:
        # Connect to MCP Router, not directly to agent
        channel = grpc.insecure_channel(f'{host}:{port}')
        stub = agent_platform_pb2_grpc.AgentServiceStub(channel)
        
        # Test ExecuteTask
        task_id = str(uuid.uuid4())
        request = agent_platform_pb2.TaskRequest(
            task_id=task_id,
            agent_id='echo-agent',  # Router will discover this agent
            input='Hello, Agent Platform!',
            parameters={'test': 'true'}
        )
        
        print(f"Sending task: {task_id}")
        response = stub.ExecuteTask(request)
        
        print(f"✓ Task completed: {response.success}")
        print(f"  Output: {response.output}")
        
        # Test GetStatus
        status_request = agent_platform_pb2.StatusRequest(agent_id='echo-agent')
        status = stub.GetStatus(status_request)
        
        print(f"✓ Agent status: {status.status}")
        print(f"  Active tasks: {status.active_tasks}")
        print(f"  Uptime: {status.uptime_seconds}s")
        
        channel.close()
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_weather_tool(host='localhost', port=50051):
    """Test the Weather Tool through MCP Router"""
    print(f"\n=== Testing Weather Tool through MCP Router at {host}:{port} ===")
    
    try:
        # Connect to MCP Router
        channel = grpc.insecure_channel(f'{host}:{port}')
        stub = agent_platform_pb2_grpc.ToolServiceStub(channel)
        
        # Test get_weather
        request = agent_platform_pb2.ToolRequest(
            tool_id='weather-tool',  # Router will discover this tool
            operation='get_weather',
            parameters={'location': 'New York'}
        )
        
        print("Getting weather for New York...")
        response = stub.ExecuteTool(request)
        
        print(f"✓ Request completed: {response.success}")
        print(f"  Result: {response.result}")
        
        # Test ListTools
        list_request = agent_platform_pb2.ListToolsRequest()
        tools = stub.ListTools(list_request)
        
        print(f"✓ Available tools: {len(tools.tools)}")
        for tool in tools.tools:
            print(f"  - {tool.name}: {tool.description}")
        
        channel.close()
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_itinerary_worker(host='localhost', port=50051):
    """Test the Itinerary Task Worker through MCP Router"""
    print(f"\n=== Testing Itinerary Worker through MCP Router at {host}:{port} ===")
    
    try:
        # Connect to MCP Router
        channel = grpc.insecure_channel(f'{host}:{port}')
        stub = agent_platform_pb2_grpc.TaskWorkerStub(channel)
        
        # Test ProcessTask
        task_id = str(uuid.uuid4())
        request = agent_platform_pb2.TaskRequest(
            task_id=task_id,
            agent_id='itinerary-worker',  # Router will discover this worker
            input='Plan a trip',
            parameters={
                'destination': 'Paris',
                'days': '3',
                'interests': 'culture,food'
            }
        )
        
        print(f"Planning itinerary for Paris (3 days)...")
        response = stub.ProcessTask(request)
        
        print(f"✓ Task completed: {response.success}")
        if response.success:
            print(f"  Destination: {response.metadata.get('destination', 'N/A')}")
            print(f"  Output preview: {response.output[:200]}...")
        
        channel.close()
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def main():
    """Run all tests through MCP Router"""
    print("=" * 60)
    print("Agent Platform - Service Tests (via MCP Router)")
    print("=" * 60)
    print("\nConnecting to MCP Router at localhost:50051")
    print("Router will discover and route to backend services via Consul")
    
    results = []
    
    # Test all services through the router
    results.append(('Echo Agent', test_echo_agent()))
    results.append(('Weather Tool', test_weather_tool()))
    results.append(('Itinerary Worker', test_itinerary_worker()))
    
    # Print summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    for service, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{status} - {service}")
    
    # Exit with appropriate code
    if all(success for _, success in results):
        print("\n✓ All tests passed!")
        sys.exit(0)
    else:
        print("\n✗ Some tests failed")
        sys.exit(1)


if __name__ == '__main__':
    main()
