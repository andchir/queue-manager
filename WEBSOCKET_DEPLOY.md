# WebSocket Server Production Deployment Guide

This guide provides comprehensive instructions for deploying the WebSocket server (`web/server.py`) in a production environment.

## Overview

The WebSocket server (`web/server.py`) is a notification center that manages real-time bidirectional communication between clients. It supports:
- Client registration with UUID-based identification
- Message routing between specific clients
- Automatic connection cleanup
- Ping/pong health checks (60s interval, 30s timeout)

## Prerequisites

### System Requirements
- Python 3.10 or higher
- Linux-based server (Ubuntu/Debian recommended)
- Supervisor (process control system)
- Nginx (for reverse proxy)
- Sudo/root access for system configuration

### Python Dependencies
The WebSocket server requires the `websockets` library, which is included in `requirements.txt`:
```bash
websockets==16.0
```

## Installation Steps

### 1. Install System Dependencies

```bash
# Update package list
sudo apt update

# Install supervisor
sudo apt install supervisor

# Enable and start supervisor
sudo systemctl enable supervisor --now

# Verify supervisor is running
sudo systemctl status supervisor
```

### 2. Install Python Dependencies

Navigate to your project directory and install dependencies:
```bash
cd /path/to/queue-manager
source venv/bin/activate  # Activate your virtual environment
pip install -r requirements.txt
```

### 3. Configure Supervisor

Supervisor will manage the WebSocket server process, ensuring it runs continuously and restarts on failures.

#### Copy the Configuration File

```bash
sudo cp web/supervisord.conf /etc/supervisor/conf.d/queue-websocket.conf
```

#### Edit the Configuration

Edit the configuration file to match your environment:
```bash
sudo nano /etc/supervisor/conf.d/queue-websocket.conf
```

Update the following paths to match your setup:

```ini
[supervisord]

[program:queue-websocket]
command=python /YOUR/PATH/TO/queue-manager/web/server.py 8765
environment=PATH="/YOUR/PATH/TO/queue-manager/venv/bin:%(ENV_PATH)s"
process_name=%(program_name)s_%(process_num)02d
numprocs=1
autostart=true
autorestart=true
user=YOUR_USERNAME
group=YOUR_USERNAME
stdout_logfile=/YOUR/PATH/TO/queue-manager/websockets-supervisord_info.log
stderr_logfile=/YOUR/PATH/TO/queue-manager/websockets-supervisord_error.log
stdout_logfile_maxbytes=100MB
stderr_logfile_maxbytes=100MB
```

**Configuration Parameters:**
- `command`: Full path to your Python executable and server script, with port number (default: 8765)
- `environment`: PATH including your virtual environment
- `numprocs`: Number of processes to run (default: 1)
- `autostart`: Start automatically when supervisor starts
- `autorestart`: Restart if the process crashes
- `user`/`group`: Linux user/group to run the process
- `stdout_logfile`/`stderr_logfile`: Log file locations

#### Reload Supervisor Configuration

```bash
# Reload supervisor to apply changes
sudo supervisorctl reread
sudo supervisorctl update

# Start the WebSocket server
sudo supervisorctl start queue-websocket:queue-websocket_00

# Verify it's running
sudo supervisorctl status
```

### 4. Configure Nginx Reverse Proxy

To expose the WebSocket server to external clients, configure Nginx as a reverse proxy.

#### Add WebSocket Upgrade Map

Edit your Nginx configuration (typically `/etc/nginx/nginx.conf`):
```bash
sudo nano /etc/nginx/nginx.conf
```

Add this map directive in the `http` block:
```nginx
http {
    # WebSocket upgrade mapping
    map $http_upgrade $connection_upgrade {
        default                     upgrade;
        ''                          close;
    }

    # ... rest of your http configuration
}
```

#### Create Server Block for WebSocket

Create a new server configuration:
```bash
sudo nano /etc/nginx/sites-available/queue-websocket
```

Add the following configuration:
```nginx
server {
    listen                      80;
    server_name                 ws.yourdomain.com;  # Replace with your domain

    server_tokens               off;
    client_body_buffer_size     0;
    client_max_body_size        0;
    large_client_header_buffers 8 32k;
    client_body_timeout         600;
    client_header_timeout       600;
    keepalive_timeout           86400;
    send_timeout                3600;

    access_log                  /var/log/nginx/ws.yourdomain.com_access.log;
    error_log                   /var/log/nginx/ws.yourdomain.com_error.log info;

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
```

#### Enable the Site and Reload Nginx

```bash
# Enable the site
sudo ln -s /etc/nginx/sites-available/queue-websocket /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx
```

### 5. Configure SSL/TLS (Recommended for Production)

For secure WebSocket connections (WSS), use Let's Encrypt:

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Obtain SSL certificate
sudo certbot --nginx -d ws.yourdomain.com

# Certbot will automatically update your Nginx configuration
```

After SSL is configured, your WebSocket server will be accessible via `wss://ws.yourdomain.com/`

## Server Configuration

### Port Configuration

The WebSocket server accepts a port number as a command-line argument:

```python
# Default port: 8765
python web/server.py

# Custom port: 9000
python web/server.py 9000
```

Update the supervisor configuration if you change the port:
```ini
command=python /path/to/queue-manager/web/server.py 9000
```

And update the Nginx proxy_pass accordingly:
```nginx
proxy_pass http://127.0.0.1:9000;
```

### Logging Configuration

The server uses Python's logging module with WARNING level by default. To change the logging level, edit `web/server.py`:

```python
# For production (minimal logging)
logging.basicConfig(level=logging.WARNING)

# For debugging
logging.basicConfig(level=logging.INFO)

# For verbose debugging
logging.basicConfig(level=logging.DEBUG)
```

## Testing the Deployment

### 1. Test Local Connection

```bash
# Using websockets Python library
python -m websockets ws://localhost:8765/
```

### 2. Test from Python Client

Use the provided client script:
```bash
python web/client.py <recipient_uuid> "Test message"
```

### 3. Test from Browser

Open `web/example.html` in a browser:
```
file:///path/to/queue-manager/web/example.html#YOUR-UUID-HERE
```

Or create a simple HTML test page:
```html
<!DOCTYPE html>
<html>
<head><title>WebSocket Test</title></head>
<body>
    <script>
        const ws = new WebSocket('ws://localhost:8765/');
        ws.onopen = () => {
            console.log('Connected');
            ws.send('{"recipient_uuid": "test-uuid", "message": "connected"}');
        };
        ws.onmessage = (event) => console.log('Received:', event.data);
        ws.onerror = (error) => console.error('Error:', error);
        ws.onclose = () => console.log('Disconnected');
    </script>
</body>
</html>
```

### 4. Test External Connection

If deployed with a domain:
```bash
# Using websockets library
python -m websockets ws://ws.yourdomain.com/

# Or with SSL
python -m websockets wss://ws.yourdomain.com/
```

## Monitoring and Maintenance

### Check Process Status

```bash
# Check if the WebSocket server is running
sudo supervisorctl status queue-websocket:queue-websocket_00

# View all supervisor processes
sudo supervisorctl status
```

### View Logs

```bash
# Real-time log viewing (info log)
tail -f /path/to/queue-manager/websockets-supervisord_info.log

# Real-time log viewing (error log)
tail -f /path/to/queue-manager/websockets-supervisord_error.log

# View Nginx access logs
sudo tail -f /var/log/nginx/ws.yourdomain.com_access.log

# View Nginx error logs
sudo tail -f /var/log/nginx/ws.yourdomain.com_error.log
```

### Control the Server

```bash
# Start the server
sudo supervisorctl start queue-websocket:queue-websocket_00

# Stop the server
sudo supervisorctl stop queue-websocket:queue-websocket_00

# Restart the server
sudo supervisorctl restart queue-websocket:queue-websocket_00

# Reload after configuration changes
sudo supervisorctl reload queue-websocket:queue-websocket_00
```

### Update the Server

When updating the server code:

```bash
# 1. Pull latest changes
cd /path/to/queue-manager
git pull

# 2. Update dependencies if needed
source venv/bin/activate
pip install -r requirements.txt

# 3. Restart the server
sudo supervisorctl restart queue-websocket:queue-websocket_00

# 4. Check status
sudo supervisorctl status queue-websocket:queue-websocket_00
```

## Troubleshooting

### Server Won't Start

1. Check supervisor logs:
```bash
sudo tail -50 /path/to/queue-manager/websockets-supervisord_error.log
```

2. Verify Python path and virtual environment:
```bash
/path/to/queue-manager/venv/bin/python --version
```

3. Check if port is already in use:
```bash
sudo lsof -i :8765
sudo netstat -tulpn | grep 8765
```

4. Verify permissions:
```bash
ls -la /path/to/queue-manager/web/server.py
```

### Connection Issues

1. Check if server is listening:
```bash
sudo netstat -tulpn | grep 8765
```

2. Test local connection:
```bash
curl -i -N -H "Connection: Upgrade" -H "Upgrade: websocket" http://localhost:8765/
```

3. Check firewall:
```bash
sudo ufw status
sudo ufw allow 8765  # If firewall is blocking
```

4. Verify Nginx is proxying correctly:
```bash
sudo nginx -t
sudo tail -f /var/log/nginx/error.log
```

### High Memory/CPU Usage

1. Check the number of active connections:
```bash
# View server logs to see connection count
tail -100 /path/to/queue-manager/websockets-supervisord_info.log | grep "Connections total"
```

2. Consider running multiple processes if needed (edit supervisor config):
```ini
numprocs=4  # Run 4 processes
```

### Connection Drops

The server implements ping/pong with these defaults:
- `ping_interval=60` (seconds)
- `ping_timeout=30` (seconds)

If connections drop frequently, adjust these in `web/server.py`:
```python
async with websockets.serve(
    register,
    host='',
    port=port,
    reuse_port=True,
    ping_interval=120,  # Increase if needed
    ping_timeout=60      # Increase if needed
):
```

Then restart the server after making changes.

## Security Considerations

1. **Use SSL/TLS in production**: Always use WSS (WebSocket Secure) for production deployments
2. **Firewall configuration**: Limit access to the WebSocket port (8765) to only Nginx
3. **Authentication**: The server currently doesn't implement authentication. Consider adding authentication at the application level
4. **Rate limiting**: Implement rate limiting in Nginx to prevent abuse
5. **Monitoring**: Set up monitoring for unusual connection patterns

### Example Nginx Rate Limiting

```nginx
http {
    # Define rate limit zone (10 requests per second per IP)
    limit_req_zone $binary_remote_addr zone=ws_limit:10m rate=10r/s;

    server {
        location / {
            limit_req zone=ws_limit burst=20 nodelay;
            # ... rest of configuration
        }
    }
}
```

## Architecture Overview

### Server Components

- **CONNECTIONS**: Dictionary mapping UUID/temp_UUID to WebSocket connections
- **WS_TO_KEY**: Reverse mapping for O(1) connection cleanup
- **register()**: Main handler for WebSocket connections
- **main()**: Server initialization and signal handling

### Message Protocol

The server accepts messages in two formats:

1. **Plain text**: Simple string messages
2. **JSON**: Structured messages with recipient routing

JSON message format:
```json
{
    "recipient_uuid": "target-client-uuid",
    "message": "your message content"
}
```

### Connection Flow

1. Client connects → Server assigns temporary UUID
2. Server sends welcome message
3. Client sends `connected` message with permanent UUID
4. Server maps permanent UUID to connection
5. Messages can now be routed to this UUID
6. On disconnect, both mappings are cleaned up

## Performance Tuning

### Operating System Limits

For high-concurrency deployments, increase system limits:

```bash
# Edit limits configuration
sudo nano /etc/security/limits.conf
```

Add:
```
*    soft    nofile    65535
*    hard    nofile    65535
```

### Supervisor Configuration

For multiple worker processes:
```ini
numprocs=4  # Run 4 processes
process_name=%(program_name)s_%(process_num)02d
```

### Nginx Tuning

```nginx
worker_processes auto;
worker_connections 4096;
```

## Alternative Deployment: Systemd Service

If you prefer systemd over supervisor, create a systemd service file:

```bash
sudo nano /etc/systemd/system/queue-websocket.service
```

```ini
[Unit]
Description=Queue Manager WebSocket Server
After=network.target

[Service]
Type=simple
User=YOUR_USERNAME
Group=YOUR_USERNAME
WorkingDirectory=/path/to/queue-manager
Environment="PATH=/path/to/queue-manager/venv/bin"
ExecStart=/path/to/queue-manager/venv/bin/python /path/to/queue-manager/web/server.py 8765
Restart=always
RestartSec=10
StandardOutput=append:/path/to/queue-manager/websockets.log
StandardError=append:/path/to/queue-manager/websockets-error.log

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable queue-websocket.service
sudo systemctl start queue-websocket.service
sudo systemctl status queue-websocket.service
```

## Quick Reference

### Common Commands

```bash
# Start
sudo supervisorctl start queue-websocket:queue-websocket_00

# Stop
sudo supervisorctl stop queue-websocket:queue-websocket_00

# Restart
sudo supervisorctl restart queue-websocket:queue-websocket_00

# Status
sudo supervisorctl status

# Logs
tail -f /path/to/queue-manager/websockets-supervisord_info.log
tail -f /path/to/queue-manager/websockets-supervisord_error.log

# Test connection
python -m websockets ws://localhost:8765/

# Test with client
python web/client.py <uuid> "Test message"
```

## Additional Resources

- [websockets library documentation](https://websockets.readthedocs.io/)
- [Supervisor documentation](http://supervisord.org/)
- [Nginx WebSocket proxying](https://nginx.org/en/docs/http/websocket.html)
- [Let's Encrypt](https://letsencrypt.org/)

## Support

For issues specific to the WebSocket server implementation, please refer to:
- `web/server.py` - Server implementation
- `web/client.py` - Client example
- `web/example.html` - Browser client example
