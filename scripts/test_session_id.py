#!/usr/bin/env python3
"""
Test session ID functionality across all services
"""

import grpc
import sys
import os
import uuid

# Add proto to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'proto'))

import agent_platform_pb2
import agent_platform_pb2_grpc


def test_echo_agent_session():
    """Test session ID with echo agent"""
    print("\n" + "="*70)
    print("Testing Echo Agent with Session ID")
    print("="*70)
    
    channel = grpc.insecure_channel('localhost:50051')
    stub = agent_platform_pb2_grpc.AgentServiceStub(channel)
    
    # Generate session ID
    session_id = str(uuid.uuid4())
    print(f"\n📝 Generated Session ID: {session_id}")
    
    # First request
    print("\n🔵 Request 1 - First message in session")
    request1 = agent_platform_pb2.TaskRequest(
        task_id=str(uuid.uuid4()),
        agent_id='echo-agent',
        input='First message in session',
        parameters={},
        session_id=session_id
    )
    
    try:
        response1 = stub.ExecuteTask(request1)
        print(f"   ✓ Success: {response1.success}")
        print(f"   ✓ Output: {response1.output}")
        print(f"   ✓ Session ID returned: {response1.session_id}")
        print(f"   ✓ Metadata: {dict(response1.metadata)}")
        
        assert response1.session_id == session_id, "Session ID mismatch!"
        print("   ✅ Session ID matches!")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        channel.close()
        return False
    
    # Second request (same session)
    print("\n🔵 Request 2 - Second message in same session")
    request2 = agent_platform_pb2.TaskRequest(
        task_id=str(uuid.uuid4()),
        agent_id='echo-agent',
        input='Second message in same session',
        parameters={'context': 'remember_me'},
        session_id=session_id
    )
    
    try:
        response2 = stub.ExecuteTask(request2)
        print(f"   ✓ Success: {response2.success}")
        print(f"   ✓ Output: {response2.output}")
        print(f"   ✓ Session ID returned: {response2.session_id}")
        print(f"   ✓ Metadata: {dict(response2.metadata)}")
        
        assert response2.session_id == session_id, "Session ID mismatch!"
        print("   ✅ Session ID matches!")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        channel.close()
        return False
    
    channel.close()
    print("\n✅ Echo Agent Session ID Test Passed!\n")
    return True


def test_weather_tool_session():
    """Test session ID with weather tool"""
    print("\n" + "="*70)
    print("Testing Weather Tool with Session ID")
    print("="*70)
    
    channel = grpc.insecure_channel('localhost:50051')
    stub = agent_platform_pb2_grpc.ToolServiceStub(channel)
    
    # Generate session ID
    session_id = str(uuid.uuid4())
    print(f"\n📝 Generated Session ID: {session_id}")
    
    print("\n🔵 Request - Get weather with session")
    request = agent_platform_pb2.ToolRequest(
        tool_id='weather-tool',
        operation='get_weather',
        parameters={'location': 'New York'},
        session_id=session_id
    )
    
    try:
        response = stub.ExecuteTool(request)
        print(f"   ✓ Success: {response.success}")
        print(f"   ✓ Result: {response.result[:100]}...")
        print(f"   ✓ Session ID returned: {response.session_id}")
        
        assert response.session_id == session_id, "Session ID mismatch!"
        print("   ✅ Session ID matches!")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        channel.close()
        return False
    
    channel.close()
    print("\n✅ Weather Tool Session ID Test Passed!\n")
    return True


def test_itinerary_worker_session():
    """Test session ID with itinerary worker"""
    print("\n" + "="*70)
    print("Testing Itinerary Worker with Session ID")
    print("="*70)
    
    channel = grpc.insecure_channel('localhost:50051')
    stub = agent_platform_pb2_grpc.TaskWorkerStub(channel)
    
    # Generate session ID
    session_id = str(uuid.uuid4())
    print(f"\n📝 Generated Session ID: {session_id}")
    
    print("\n🔵 Request - Plan itinerary with session")
    request = agent_platform_pb2.TaskRequest(
        task_id=str(uuid.uuid4()),
        agent_id='itinerary-worker',
        input='Plan my trip',
        parameters={
            'destination': 'Paris',
            'days': '3',
            'interests': 'culture,food'
        },
        session_id=session_id
    )
    
    try:
        response = stub.ProcessTask(request)
        print(f"   ✓ Success: {response.success}")
        print(f"   ✓ Output length: {len(response.output)} chars")
        print(f"   ✓ Session ID returned: {response.session_id}")
        print(f"   ✓ Metadata: {dict(response.metadata)}")
        
        assert response.session_id == session_id, "Session ID mismatch!"
        print("   ✅ Session ID matches!")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        channel.close()
        return False
    
    channel.close()
    print("\n✅ Itinerary Worker Session ID Test Passed!\n")
    return True


def test_streaming_session():
    """Test session ID with streaming (echo agent)"""
    print("\n" + "="*70)
    print("Testing Streaming with Session ID")
    print("="*70)
    
    channel = grpc.insecure_channel('localhost:50051')
    stub = agent_platform_pb2_grpc.AgentServiceStub(channel)
    
    # Generate session ID
    session_id = str(uuid.uuid4())
    print(f"\n📝 Generated Session ID: {session_id}")
    
    print("\n🔵 Streaming Request")
    request = agent_platform_pb2.TaskRequest(
        task_id=str(uuid.uuid4()),
        agent_id='echo-agent',
        input='Hello streaming world with session',
        parameters={},
        session_id=session_id
    )
    
    try:
        chunks = []
        for chunk in stub.StreamTask(request):
            print(f"   ✓ Chunk: {chunk.content} (final: {chunk.is_final})")
            print(f"     Session ID: {chunk.session_id}")
            chunks.append(chunk)
            assert chunk.session_id == session_id, "Session ID mismatch in chunk!"
        
        print(f"   ✅ Received {len(chunks)} chunks, all with correct session ID!")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        channel.close()
        return False
    
    channel.close()
    print("\n✅ Streaming Session ID Test Passed!\n")
    return True


def test_without_session_id():
    """Test that services work without session ID (backward compatibility)"""
    print("\n" + "="*70)
    print("Testing Backward Compatibility (No Session ID)")
    print("="*70)
    
    channel = grpc.insecure_channel('localhost:50051')
    stub = agent_platform_pb2_grpc.AgentServiceStub(channel)
    
    print("\n🔵 Request without session ID")
    request = agent_platform_pb2.TaskRequest(
        task_id=str(uuid.uuid4()),
        agent_id='echo-agent',
        input='Message without session',
        parameters={}
        # No session_id provided
    )
    
    try:
        response = stub.ExecuteTask(request)
        print(f"   ✓ Success: {response.success}")
        print(f"   ✓ Output: {response.output}")
        print(f"   ✓ Session ID: '{response.session_id}' (empty is OK)")
        print("   ✅ Works without session ID!")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        channel.close()
        return False
    
    channel.close()
    print("\n✅ Backward Compatibility Test Passed!\n")
    return True


def main():
    """Run all session ID tests"""
    print("\n" + "="*70)
    print("SESSION ID FUNCTIONALITY TEST SUITE")
    print("="*70)
    print("\nThis test suite verifies that session_id is properly handled")
    print("across all services in the agent platform.\n")
    
    results = []
    
    # Run tests
    tests = [
        ("Echo Agent", test_echo_agent_session),
        ("Weather Tool", test_weather_tool_session),
        ("Itinerary Worker", test_itinerary_worker_session),
        ("Streaming", test_streaming_session),
        ("Backward Compatibility", test_without_session_id),
    ]
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ Test '{test_name}' crashed: {e}")
            results.append((test_name, False))
    
    # Print summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70 + "\n")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {test_name}")
    
    print(f"\n{passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Session ID implementation is working correctly.\n")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please review the output above.\n")
        return 1


if __name__ == '__main__':
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}\n")
        sys.exit(1)

