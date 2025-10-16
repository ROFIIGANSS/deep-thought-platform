#!/usr/bin/env python3
"""
Simple example client demonstrating Agent Platform usage
"""

import grpc
import sys
import os
import uuid
import json

# Add proto to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'proto'))

try:
    import agent_platform_pb2
    import agent_platform_pb2_grpc
except ImportError:
    print("Error: Proto files not compiled. Run: bash scripts/compile_proto.sh")
    sys.exit(1)


def example_echo_agent():
    """Example: Using the Echo Agent"""
    print("\n" + "="*60)
    print("Example 1: Echo Agent")
    print("="*60)
    
    # Connect to Echo Agent
    channel = grpc.insecure_channel('localhost:50052')
    stub = agent_platform_pb2_grpc.AgentServiceStub(channel)
    
    # Create a task
    task_id = str(uuid.uuid4())
    request = agent_platform_pb2.TaskRequest(
        task_id=task_id,
        agent_id='echo-agent',
        input='Hello from the Agent Platform!',
        parameters={
            'priority': 'high',
            'source': 'example_client'
        }
    )
    
    print(f"\n📤 Sending task to Echo Agent...")
    print(f"   Task ID: {task_id}")
    print(f"   Input: {request.input}")
    
    # Execute task
    response = stub.ExecuteTask(request)
    
    print(f"\n📥 Received response:")
    print(f"   Success: {response.success}")
    print(f"   Output: {response.output}")
    print(f"   Metadata: {dict(response.metadata)}")
    
    channel.close()


def example_weather_tool():
    """Example: Using the Weather Tool"""
    print("\n" + "="*60)
    print("Example 2: Weather Tool")
    print("="*60)
    
    # Connect to Weather Tool
    channel = grpc.insecure_channel('localhost:50053')
    stub = agent_platform_pb2_grpc.ToolServiceStub(channel)
    
    # Get current weather
    print("\n🌤️  Getting weather for New York...")
    request = agent_platform_pb2.ToolRequest(
        tool_id='weather-tool',
        operation='get_weather',
        parameters={'location': 'New York'}
    )
    
    response = stub.ExecuteTool(request)
    
    if response.success:
        weather = json.loads(response.result)
        print(f"\n   Location: {weather['location']}")
        print(f"   Temperature: {weather['temperature']}°F")
        print(f"   Condition: {weather['condition']}")
        print(f"   Humidity: {weather['humidity']}%")
    else:
        print(f"   Error: {response.error}")
    
    # Get forecast
    print("\n🌤️  Getting 5-day forecast for London...")
    forecast_request = agent_platform_pb2.ToolRequest(
        tool_id='weather-tool',
        operation='get_forecast',
        parameters={'location': 'London', 'days': '5'}
    )
    
    forecast_response = stub.ExecuteTool(forecast_request)
    
    if forecast_response.success:
        forecast = json.loads(forecast_response.result)
        print(f"\n   5-Day Forecast for London:")
        for day in forecast[:3]:  # Show first 3 days
            print(f"   Day {day['day']}: {day['temperature']}°F, {day['condition']}")
    
    channel.close()


def example_itinerary_worker():
    """Example: Using the Itinerary Task Worker"""
    print("\n" + "="*60)
    print("Example 3: Itinerary Task Worker")
    print("="*60)
    
    # Connect to Itinerary Worker
    channel = grpc.insecure_channel('localhost:50054')
    stub = agent_platform_pb2_grpc.TaskWorkerStub(channel)
    
    # Plan a trip
    print("\n✈️  Planning a 3-day trip to Paris...")
    task_id = str(uuid.uuid4())
    request = agent_platform_pb2.TaskRequest(
        task_id=task_id,
        agent_id='itinerary-worker',
        input='Plan an amazing vacation',
        parameters={
            'destination': 'Paris',
            'days': '3',
            'interests': 'culture,food,art'
        }
    )
    
    response = stub.ProcessTask(request)
    
    if response.success:
        itinerary = json.loads(response.output)
        
        print(f"\n   Destination: {itinerary['destination']}")
        print(f"   Duration: {itinerary['total_days']} days")
        print(f"   Interests: {', '.join(itinerary['interests'])}")
        
        print(f"\n   📅 Daily Schedule:")
        for day in itinerary['daily_schedule'][:2]:  # Show first 2 days
            print(f"\n   Day {day['day']} ({day['date']}):")
            if day.get('morning'):
                print(f"      🌅 Morning: {day['morning']['activity']}")
            if day.get('afternoon'):
                print(f"      ☀️  Afternoon: {day['afternoon']['activity']}")
            if day.get('evening'):
                print(f"      🌙 Evening: {day['evening']['activity']}")
        
        print(f"\n   🏨 Accommodation:")
        print(f"      Hotel: {itinerary['accommodation']['hotel']}")
        print(f"      Check-in: {itinerary['accommodation']['check_in']}")
        print(f"      Check-out: {itinerary['accommodation']['check_out']}")
        
        print(f"\n   ✅ Optimizations Applied:")
        for note in itinerary.get('optimization_notes', []):
            print(f"      • {note}")
    else:
        print(f"   Error: {response.error}")
    
    channel.close()


def example_streaming():
    """Example: Streaming responses from Echo Agent"""
    print("\n" + "="*60)
    print("Example 4: Streaming Response")
    print("="*60)
    
    # Connect to Echo Agent
    channel = grpc.insecure_channel('localhost:50052')
    stub = agent_platform_pb2_grpc.AgentServiceStub(channel)
    
    # Create a streaming task
    task_id = str(uuid.uuid4())
    request = agent_platform_pb2.TaskRequest(
        task_id=task_id,
        agent_id='echo-agent',
        input='This is a streaming test with multiple words'
    )
    
    print(f"\n📤 Sending streaming task...")
    print(f"   Receiving words one at a time:\n")
    
    # Stream response
    print("   ", end='', flush=True)
    for chunk in stub.StreamTask(request):
        if not chunk.is_final:
            print(f"{chunk.content} ", end='', flush=True)
        else:
            print(f"\n\n   {chunk.content}")
    
    channel.close()


def main():
    """Run all examples"""
    print("\n" + "="*60)
    print("Agent Platform - Example Client")
    print("="*60)
    print("\nThis script demonstrates various platform capabilities:\n")
    print("1. Echo Agent - Basic task execution")
    print("2. Weather Tool - External tool usage")
    print("3. Itinerary Worker - Complex task processing")
    print("4. Streaming - Real-time response streaming")
    
    try:
        # Run examples
        example_echo_agent()
        example_weather_tool()
        example_itinerary_worker()
        example_streaming()
        
        # Summary
        print("\n" + "="*60)
        print("✓ All examples completed successfully!")
        print("="*60)
        print("\nNext Steps:")
        print("  • Modify these examples for your use case")
        print("  • Create your own agents and tools")
        print("  • Check out QUICKSTART.md for more info")
        print("  • View the Consul UI at http://localhost:8500")
        print("")
        
    except grpc.RpcError as e:
        print(f"\n❌ Error: {e.code()}: {e.details()}")
        print("\nMake sure all services are running:")
        print("  docker-compose ps")
        print("\nOr start them with:")
        print("  docker-compose up -d")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()

