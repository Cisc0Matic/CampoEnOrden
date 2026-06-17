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
