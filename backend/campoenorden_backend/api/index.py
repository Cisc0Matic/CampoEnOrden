import os
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'campoenorden_backend.settings.production')

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()

app = application
