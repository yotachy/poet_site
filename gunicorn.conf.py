# gunicorn 운영 서버 설정
bind = "0.0.0.0:8000"
workers = 2
worker_class = "sync"
timeout = 60
keepalive = 5
accesslog = "-"
errorlog  = "-"
loglevel  = "info"
