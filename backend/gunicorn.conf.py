"""This file contains the gunicorn configuration required for the API Server."""

bind = "0.0.0.0:4003"

# Worker Options
worker_class = "uvicorn.workers.UvicornWorker"
workers = 4

# Timeout Options
timeout = 300
graceful_timeout = 300

# Other Options
keepalive = 5
