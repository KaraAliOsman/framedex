"""Railway Linux WSGI process; bounded graceful shutdown and no sensitive URL logs."""

import os

bind = '0.0.0.0:' + os.environ.get('PORT', '8000')
workers = int(os.environ.get('WEB_CONCURRENCY', '2'))
worker_class = 'gthread'
threads = 4
timeout = 120
graceful_timeout = 30
keepalive = 5
max_requests = 1000
max_requests_jitter = 100
accesslog = None
errorlog = '-'
capture_output = True
