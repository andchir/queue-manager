import sys
import os

sys.path.append(os.path.abspath('.'))
from config import settings


def remove_outdated_queue_items():
    max_execution_time = settings.max_execution_time
    print(max_execution_time, type(max_execution_time))


if __name__ == '__main__':
    remove_outdated_queue_items()
