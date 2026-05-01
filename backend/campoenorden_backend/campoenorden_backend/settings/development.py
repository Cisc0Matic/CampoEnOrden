from .base import *

DEBUG = True

ALLOWED_HOSTS = ['*'] # Allow all hosts for development

# You might want to override other settings here for development
# For example, a different database or email backend
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
