import os

from .base import *

DEBUG = False

ALLOWED_HOSTS = [
    h.strip() for h in os.environ.get('ALLOWED_HOSTS', '.vercel.app,localhost,127.0.0.1').split(',') if h.strip()
]

SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', SECRET_KEY)

FRONTEND_URL = os.environ.get('FRONTEND_URL', 'https://campoenorden.netlify.app')

CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = os.environ.get(
    'CORS_ALLOWED_ORIGINS',
    'https://campoenorden.netlify.app,https://campoenorden-admin.netlify.app,http://localhost:8100',
).split(',')
# Previews/deploys temporales de Netlify (xxx--<hash>.netlify.app)
CORS_ALLOWED_ORIGIN_REGEXES = [
    r'^https://[\w-]+\.netlify\.app$',
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('PGDATABASE', ''),
        'USER': os.environ.get('PGUSER', ''),
        'PASSWORD': os.environ.get('PGPASSWORD', ''),
        'HOST': os.environ.get('PGHOST', ''),
        'PORT': os.environ.get('PGPORT', '5432'),
    }
}

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# HTTPS detrás del túnel/nginx: gated por DJANGO_HTTPS=1 cuando haya dominio fijo.
# Mientras tanto el túnel ya manda X-Forwarded-Proto: https y el redirect no
# hace falta en el origen (riesgo de loop si se fuerza en HTTP puro).
_https_enabled = os.environ.get('DJANGO_HTTPS', '0') == '1'
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = _https_enabled
SESSION_COOKIE_SECURE = _https_enabled
CSRF_COOKIE_SECURE = _https_enabled