# Mia Dental OS — public deployment image.
#
# Stdlib-only Python: nothing to pip install. The server reads $PORT
# (injected by Render/Fly), binds PRESCRIBE_HOST, and keeps its SQLite
# databases on the /data volume (set PRESCRIBE_DB / PRESCRIBE_STATE_DIR).
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PRESCRIBE_HOST=0.0.0.0 \
    PRESCRIBE_DB=/data/prescribe.sqlite3 \
    PRESCRIBE_STATE_DIR=/data \
    PRESCRIBE_SECURE_COOKIES=1

WORKDIR /app

# Package layout: python -m ai_front_desk.clinical.prescribe.server
COPY ai_front_desk/ ./ai_front_desk/
# Legal docs are rendered by the app at runtime (/legal, /privacy, /terms).
COPY docs/legal/ ./docs/legal/

RUN useradd --create-home --shell /usr/sbin/nologin mia \
    && mkdir -p /data \
    && chown -R mia:mia /app /data

USER mia

EXPOSE 8767

CMD ["python", "-m", "ai_front_desk.clinical.prescribe.server"]
