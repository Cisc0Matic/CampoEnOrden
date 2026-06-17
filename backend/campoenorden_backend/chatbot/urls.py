from django.conf import settings
from django.urls import path

from .views import WhatsAppWebhookView

urlpatterns = [
    path('webhook/', WhatsAppWebhookView.as_view(), name='whatsapp_webhook'),
]

if settings.DEBUG:
    from .test_views import SimulatorView
    urlpatterns += [
        path('sim/', SimulatorView.as_view(), name='chatbot_simulator'),
    ]

from django.db import connection
from django.http import JsonResponse

def _db_check(request):
    tables = {}
    for table in ['chatbot_maquinaria', 'core_campo', 'core_lote', 'users_user']:
        try:
            with connection.cursor() as cursor:
                cursor.execute(f'SELECT COUNT(*) FROM {table}')
                tables[table] = {'exists': True, 'count': cursor.fetchone()[0]}
        except Exception as e:
            tables[table] = {'exists': False, 'error': str(e)}
    return JsonResponse({'tables': tables})

urlpatterns += [
    path('db-check/', _db_check, name='db_check'),
]

