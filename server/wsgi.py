"""Entry point of the EKARUSwiki server.

  Development / testing:  python -m flask --app wsgi run --port 5000
  Production (Linux):     gunicorn --workers 2 --bind 127.0.0.1:8000 wsgi:app

Settings are read from the .env file in this folder (see .env.example).
"""
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:      # python-dotenv not installed: use environment variables only
    pass

from ekaruswiki import create_app

app = create_app()
