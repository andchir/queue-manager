# Simple task queue manager

Start in development mode:
~~~
uvicorn main:app --reload
~~~

Docs:
~~~
http://127.0.0.1:8000/docs
http://127.0.0.1:8000/redoc
~~~

Migrations:
~~~
alembic history --verbose
alembic revision --autogenerate -m "Added tasks table"
alembic upgrade head
~~~

Install SQLite on Ubuntu:
~~~
wget https://sqlite.org/2024/sqlite-autoconf-3450100.tar.gz
tar -xvf sqlite-autoconf-3450100.tar.gz && cd sqlite-autoconf-3450100
sudo apt-get install libreadline-dev
./configure
make
sudo apt purge sqlite3
sudo make install
sqlite3 --version
~~~

Create SQLite database:
~~~
sqlite3 app_database.db
.databases
.quit
~~~

Update Python sqlite3 module:
~~~
ldd `find /usr/lib/python3.10/ -name '_sqlite3*'` | grep sqlite
cd sqlite-autoconf-3450100/.libs
sudo cp /lib/x86_64-linux-gnu/libsqlite3.so.0 ./backup/libsqlite3.so.0
sudo cp libsqlite3.so.0 /lib/x86_64-linux-gnu/libsqlite3.so.0
python3.10 -c "import sqlite3; print(sqlite3.sqlite_version)"
~~~

Generate API key:
~~~
python -c "import uuid; print(str(uuid.uuid4()))"
~~~
Add it to .env (API_KEYS).
