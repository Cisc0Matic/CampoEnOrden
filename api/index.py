import os
import sys

ROOT = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, os.path.join(ROOT, 'backend', 'campoenorden_backend'))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'campoenorden_backend.settings.production')

_application = None


def get_app():
    global _application
    if _application is None:
        from django.core.wsgi import get_wsgi_application
        _application = get_wsgi_application()
    return _application


def application(environ, start_response):
    try:
        app = get_app()
        return app(environ, start_response)
    except Exception:
        import traceback
        tb = traceback.format_exc()
        status = '500 Internal Server Error'
        headers = [('Content-Type', 'text/plain; charset=utf-8')]
        start_response(status, headers)
        return [tb.encode()]


app = application
