"""
Simple test to verify retry parameters are correctly set in queue_manager functions.
This test doesn't require full dependencies.
"""

import re


def test_retry_parameters_present():
    """Verify that retry parameters are present in send functions"""

    with open('utils/queue_manager.py', 'r') as f:
        content = f.read()

    # Check send_queue_result has retry parameters
    assert re.search(r'def send_queue_result\([^)]*retry_delay\s*=\s*20', content), \
        "send_queue_result should have retry_delay=20 parameter"

    assert re.search(r'def send_queue_result\([^)]*max_retries\s*=\s*10', content), \
        "send_queue_result should have max_retries=10 parameter"

    # Check send_queue_result_dict has retry parameters
    assert re.search(r'def send_queue_result_dict\([^)]*retry_delay\s*=\s*20', content), \
        "send_queue_result_dict should have retry_delay=20 parameter"

    assert re.search(r'def send_queue_result_dict\([^)]*max_retries\s*=\s*10', content), \
        "send_queue_result_dict should have max_retries=10 parameter"

    # Check send_queue_error has retry parameters
    assert re.search(r'def send_queue_error\([^)]*retry_delay\s*=\s*20', content), \
        "send_queue_error should have retry_delay=20 parameter"

    assert re.search(r'def send_queue_error\([^)]*max_retries\s*=\s*10', content), \
        "send_queue_error should have max_retries=10 parameter"

    # Check retry logic implementation with for loop
    assert content.count('for attempt in range(max_retries + 1):') >= 3, \
        "Expected at least 3 retry loops (one for each send function)"

    # Check sleep is called for retry delay
    assert content.count('time.sleep(retry_delay)') >= 3, \
        "Expected at least 3 sleep calls for retry delays"

    # Check error messages mention retry
    assert 'Retrying in' in content, \
        "Error messages should mention retrying"

    print("✓ All retry parameters are correctly set")
    print("✓ send_queue_result has retry_delay=20 and max_retries=10")
    print("✓ send_queue_result_dict has retry_delay=20 and max_retries=10")
    print("✓ send_queue_error has retry_delay=20 and max_retries=10")
    print("✓ Retry logic implemented with proper loops and delays")


if __name__ == '__main__':
    try:
        test_retry_parameters_present()
        print("\nAll verification tests passed!")
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        exit(1)
