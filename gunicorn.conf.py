import os

# PDF routes call XeLaTeX, which may run several times. Stay above that budget
# so a slow compile returns an application error instead of a worker kill.
bind = "0.0.0.0:8000"
workers = int(os.environ.get("GUNICORN_WORKERS", "2"))
timeout = int(os.environ.get("GUNICORN_TIMEOUT", "330"))
graceful_timeout = 30
accesslog = "-"
errorlog = "-"
capture_output = True
