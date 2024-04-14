import sys
import os
import datetime

sys.path.append(os.path.abspath('.'))
from config import settings
from db.db import session_maker
from models.queue import QueueStatus
from repositories.queue_repository import QueueRepository


def restore_outdated_queue_items():
    max_execution_time = settings.max_execution_time
    now = datetime.datetime.utcnow()
    outdated_ids = []

    with session_maker() as session:
        queue_repository = QueueRepository(session)
        res = queue_repository.find_by_status(QueueStatus.PROCESSING.value)
        for queue in res:
            if (now - queue[0].time_updated).total_seconds() > max_execution_time:
                outdated_ids.append(queue[0].id)

    for item_id in outdated_ids:
        with session_maker() as session:
            queue_repository = QueueRepository(session)
            result = queue_repository.update_one({
                'status': QueueStatus.PENDING.value,
                'time_updated': datetime.datetime.utcnow()
            }, item_id)

    return outdated_ids


if __name__ == '__main__':
    result = restore_outdated_queue_items()
    print(result)
