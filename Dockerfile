FROM python:3.12-slim-bookworm
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz-subset0 libjpeg62-turbo libopenjp2-7 \
    fonts-dejavu-core && rm -rf /var/lib/apt/lists/*
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt
COPY engine /app/engine
RUN pip install --no-cache-dir ./engine
COPY backend /app/backend
RUN useradd --create-home --uid 10001 dekopen
USER 10001
ENV PYTHONPATH=/app/backend
CMD ["gunicorn", "--config", "backend/config/gunicorn.conf.py", "config.wsgi:application"]
