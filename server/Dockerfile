# EKARUSwiki server (observation schedule site, admin, team sign-in, wiki API)
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ekaruswiki ./ekaruswiki
COPY wsgi.py .

# Run as an ordinary user, not root. UID 1000 is the first user on most Linux PCs, so the
# mounted instance/ folder stays writable for you and for the container.
RUN useradd --uid 1000 --create-home app && mkdir -p /app/instance && chown app /app/instance
USER app

# Database and (without SMTP) the e-mail outbox live here: mount it from the host.
VOLUME /app/instance
EXPOSE 8000

HEALTHCHECK --interval=60s --timeout=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/account/login', timeout=4)"

CMD ["gunicorn", "--workers", "2", "--bind", "0.0.0.0:8000", "--access-logfile", "-", "wsgi:app"]
