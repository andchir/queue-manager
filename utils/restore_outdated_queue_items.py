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
    restore_ids = []
    remove_ids = []

    with session_maker() as session:
        queue_repository = QueueRepository(session)
        res = queue_repository.find_by_status(QueueStatus.PROCESSING.value)
        for queue in res:
            if (now - queue[0].time_updated).total_seconds() > max_execution_time:
                if (now - queue[0].time_created).total_seconds() > max_execution_time:
                    remove_ids.append(queue[0].id)
                else:
                    restore_ids.append(queue[0].id)

    for item_id in restore_ids:
        with session_maker() as session:
            queue_repository = QueueRepository(session)
            queue_repository.update_one({
                'status': QueueStatus.PENDING.value,
                'time_updated': datetime.datetime.utcnow()
            }, item_id)

    for item_id in remove_ids:
        with session_maker() as session:
            queue_repository = QueueRepository(session)
            queue_repository.delete(item_id)

    return restore_ids


if __name__ == '__main__':
    result = restore_outdated_queue_items()
    print(result)
