# Simple task queue manager

![screenshot #1](https://github.com/andchir/queue-manager/blob/main/screenshots/001.png?raw=true)

Start in development mode:
~~~
uvicorn main:app --reload --port=8002
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

python -c "import sqlite3; print(sqlite3.version); print(sqlite3.sqlite_version)"

https://github.com/coleifer/pysqlite3
~~~

Create SQLite database:
~~~
sqlite3 app_database.db
.databases
.quit

repacking it into a minimal amount of disk space:
VACUUM;
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

Nginx:
~~~
user www-data;
...
http {
    server {
        listen          80;
        server_name     127.0.0.1;
        
        location /uploads/ {
            root /home/andrew/python_projects/queue-manager;
        }
        
        location / {
            include proxy_params;
            proxy_pass http://unix:/run/queue_manager_gunicorn.sock;
            proxy_set_header   Host             $host;
            proxy_set_header   X-Real-IP        $remote_addr;
            proxy_set_header   X-Forwarded-For  $proxy_add_x_forwarded_for;
        }
    }
}
...
~~~

Services:
~~~
sudo nano /etc/systemd/system/queue_manager_server.service
sudo nano /etc/systemd/system/queue_manager_server.socket
~~~

Enable and start the socket (it will autostart at boot too):
~~~
sudo systemctl start queue_manager_server.socket
sudo systemctl enable queue_manager_server.socket
sudo systemctl enable queue_manager_server.service
~~~

~~~
service queue_manager_server status
service queue_manager_server restart

check socket:
file /run/queue_manager_gunicorn.sock

systemctl daemon-reload
~~~

WebSocket server:
~~~
sudo apt install supervisor

sudo systemctl enable supervisor --now
sudo supervisorctl avail
sudo supervisorctl status
sudo supervisorctl status queue-websocket:queue-websocket_00
sudo supervisorctl reload queue-websocket:queue-websocket_00

sudo cp web/supervisord.conf /etc/supervisor/conf.d/queue-websocket.conf

sudo systemctl status supervisor
sudo systemctl restart supervisor

python web/server.py 8765
supervisord -c web/supervisord.conf -n
python -m websockets ws://localhost:8765/
~~~

Nginx config for WebSocket:
~~~
map $http_upgrade $connection_upgrade {
    default                     upgrade;
    ''                          close;
}

server {
    server_name                 ws.mysite.com;

    server_tokens               off;
    client_body_buffer_size     0;
    client_max_body_size        0;
    large_client_header_buffers 8 32k;
    client_body_timeout         600;
    client_header_timeout       600;
    keepalive_timeout           86400;
    send_timeout                3600;

    access_log                  /var/log/nginx/ws.mysite.com_access.log;
    error_log                   /var/log/nginx/ws.mysite.com_error.log info;

    location @ws_server_local {

        proxy_pass                         http://127.0.0.1:8765;
        proxy_http_version                 1.1;
        proxy_set_header Host              $host;
        proxy_set_header X-Real-IP         $remote_addr;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header Upgrade           $http_upgrade;
        proxy_set_header Connection        $connection_upgrade;

        proxy_ignore_client_abort          on;
        proxy_connect_timeout              10080;
        proxy_send_timeout                 10080;
        proxy_read_timeout                 10080;
        proxy_buffer_size                  64k;
        proxy_buffers                      16 32k;
        proxy_busy_buffers_size            64k;
        proxy_redirect                     off;
        proxy_request_buffering            off;
        proxy_buffering                    off;
        gzip_static                        off;
    }

    location / {
        try_files                          $uri @ws_server_local;
    }
}
~~~
