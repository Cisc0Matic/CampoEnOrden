FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DJANGO_SETTINGS_MODULE=campoenorden_backend.settings.production \
    LC_ALL=C.UTF-8 \
    LANG=C.UTF-8

WORKDIR /app/backend/campoenorden_backend

COPY backend/campoenorden_backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt gunicorn

COPY backend/campoenorden_backend ./

EXPOSE 8000

ENTRYPOINT ["sh", "-c"]
CMD ["python manage.py collectstatic --noinput && exec gunicorn campoenorden_backend.wsgi:application --bind 0.0.0.0:8000 --workers 2 --timeout 90"]