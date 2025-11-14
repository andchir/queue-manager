"""
Simple test to verify timeout parameters are correctly set in queue_manager functions.
This test doesn't require full dependencies.
"""

import re


def test_timeout_parameters_present():
    """Verify that timeout parameters are present in all network functions"""

    with open('utils/queue_manager.py', 'r') as f:
        content = f.read()

    # Check get_queue_next has timeout parameter
    assert re.search(r'def get_queue_next\([^)]*timeout\s*=\s*30', content), \
        "get_queue_next should have timeout=30 parameter"

    # Check get_queue_next uses timeout in requests.get
    assert re.search(r'requests\.get\([^)]*timeout\s*=\s*timeout', content), \
        "get_queue_next should pass timeout to requests.get"

    # Check send_queue_result has timeout parameter
    assert re.search(r'def send_queue_result\([^)]*timeout\s*=\s*30', content), \
        "send_queue_result should have timeout=30 parameter"

    # Check send_queue_result_dict has timeout parameter
    assert re.search(r'def send_queue_result_dict\([^)]*timeout\s*=\s*30', content), \
        "send_queue_result_dict should have timeout=30 parameter"

    # Check send_queue_error has timeout parameter
    assert re.search(r'def send_queue_error\([^)]*timeout\s*=\s*30', content), \
        "send_queue_error should have timeout=30 parameter"

    # Count how many times timeout is used in requests
    timeout_usage = len(re.findall(r'requests\.(get|post)\([^)]*timeout\s*=', content))
    assert timeout_usage >= 4, \
        f"Expected at least 4 requests with timeout, found {timeout_usage}"

    print("✓ All timeout parameters are correctly set")
    print(f"✓ Found {timeout_usage} requests with timeout parameter")


if __name__ == '__main__':
    try:
        test_timeout_parameters_present()
        print("\nAll verification tests passed!")
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        exit(1)
