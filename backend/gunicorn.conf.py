import os

bind = f"0.0.0.0:{os.environ.get('PORT', 5002)}"
workers = 2
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100
timeout = 30
keepalive = 2
preload_app = True