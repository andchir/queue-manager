from db.db import session_maker
from repositories.queue_repository import QueueRepository


def main():
    print('hello world')
    with session_maker() as session:
        queue_repository = QueueRepository(session)
        res = queue_repository.find_one_next()
        print(res[0].id, res[0].data)


if __name__ == "__main__":
    main()
