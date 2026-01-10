"""
Simple test script to verify the application works.
Run with: python test_basic.py
"""

import requests
import json
import time

BASE_URL = "http://localhost:5001"


def print_section(title):
    """Print a section header."""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def test_create_flow():
    """Test creating a flow."""
    print_section("TEST 1: Create Flow")
    
    with open('sample_flow.json', 'r') as f:
        flow_data = json.load(f)
    
    response = requests.post(
        f"{BASE_URL}/api/flows",
        json=flow_data
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    return response.status_code == 201


def test_list_flows():
    """Test listing flows."""
    print_section("TEST 2: List Flows")
    
    response = requests.get(f"{BASE_URL}/api/flows")
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    return response.status_code == 200


def test_get_flow():
    """Test getting a specific flow."""
    print_section("TEST 3: Get Flow Details")
    
    response = requests.get(f"{BASE_URL}/api/flows/flow123")
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    return response.status_code == 200


def test_list_tasks():
    """Test listing available tasks."""
    print_section("TEST 4: List Available Tasks")
    
    response = requests.get(f"{BASE_URL}/api/tasks")
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    return response.status_code == 200


def test_execute_flow():
    """Test executing a flow."""
    print_section("TEST 5: Execute Flow")
    
    response = requests.post(
        f"{BASE_URL}/api/tasks/flows/flow123/execute",
        json={
            "input_context": {
                "batch_id": "test_batch_001",
                "source": "test"
            }
        }
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 200:
        execution_id = response.json()['data']['id']
        return True, execution_id
    
    return False, None


def test_get_execution(execution_id):
    """Test getting execution details."""
    print_section("TEST 6: Get Execution Details")
    
    response = requests.get(
        f"{BASE_URL}/api/executions/{execution_id}?include_tasks=true"
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    return response.status_code == 200


def main():
    """Run all tests."""
    print("\n" + "*" * 60)
    print("  FLOW MANAGER API TEST SUITE")
    print("  Make sure the server is running on http://localhost:5001")
    print("*" * 60)
    
    results = []
    
    try:
        # Test 1: Create flow
        results.append(("Create Flow", test_create_flow()))
        time.sleep(0.5)
        
        # Test 2: List flows
        results.append(("List Flows", test_list_flows()))
        time.sleep(0.5)
        
        # Test 3: Get flow
        results.append(("Get Flow", test_get_flow()))
        time.sleep(0.5)
        
        # Test 4: List tasks
        results.append(("List Tasks", test_list_tasks()))
        time.sleep(0.5)
        
        # Test 5: Execute flow
        success, execution_id = test_execute_flow()
        results.append(("Execute Flow", success))
        time.sleep(1)
        
        # Test 6: Get execution (if execution succeeded)
        if execution_id:
            results.append(("Get Execution", test_get_execution(execution_id)))
        
    except requests.exceptions.ConnectionError:
        print("\n ERROR: Could not connect to server!")
        print("   Make sure the Flask application is running:")
        print("   python run.py")
        return
    
    # Print summary
    print_section("TEST SUMMARY")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = " PASS" if result else "FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed!")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")


if __name__ == "__main__":
    main()
