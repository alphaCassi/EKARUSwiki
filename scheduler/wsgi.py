"""Entry point for the production server:  gunicorn wsgi:app"""
from scheduler import create_app

app = create_app()
