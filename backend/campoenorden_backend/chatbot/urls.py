from django.conf import settings
from django.urls import path

from .views import WhatsAppWebhookView
from .services.whatsapp import WhatsAppService

urlpatterns = [
    path('webhook/', WhatsAppWebhookView.as_view(), name='whatsapp_webhook'),
]

if settings.DEBUG:
    from .test_views import SimulatorView
    urlpatterns += [
        path('sim/', SimulatorView.as_view(), name='chatbot_simulator'),
    ]

from django.http import JsonResponse
from django.db import connection
from .models import WhatsAppSession
from users.models import User



def _health(request):
    """Quick health check — GET returns 200 if running. Add ?check=token to verify token too."""
    svc = WhatsAppService()
    token_ok = svc.verify_token()
    status = 200 if token_ok.get('valid') else 503
    return JsonResponse({
        'status': 'ok' if status == 200 else 'token_error',
        'meta_token': 'valid' if token_ok.get('valid') else 'invalid',
    }, status=status)

def _debug(request):
    phone = request.GET.get('phone', '')
    action = request.GET.get('action', '')
    info = {
        'settings': {
            'WHATSAPP_ACCESS_TOKEN': bool(settings.WHATSAPP_ACCESS_TOKEN),
            'WHATSAPP_PHONE_NUMBER_ID': bool(settings.WHATSAPP_PHONE_NUMBER_ID),
            'WHATSAPP_WEBHOOK_VERIFY_TOKEN': settings.WHATSAPP_WEBHOOK_VERIFY_TOKEN,
            'WHATSAPP_APP_SECRET': bool(settings.WHATSAPP_APP_SECRET),
            'FACEBOOK_APP_ID': bool(settings.FACEBOOK_APP_ID),
            'FACEBOOK_APP_SECRET': bool(settings.FACEBOOK_APP_SECRET),
            'DEBUG': settings.DEBUG,
        },
        'token_check': {},
        'sessions': [],
        'users': [],
    }
    if action == 'check_token':
        svc = WhatsAppService()
        info['token_check'] = svc.verify_token()
    if action == 'test_dni':
        dni = request.GET.get('dni', '')
        user = User.objects.filter(dni=dni).first()
        info['dni_test'] = {
            'dni': dni,
            'found': user is not None,
            'user_id': user.id if user else None,
            'username': user.username if user else None,
            'is_active': user.is_active if user else None,
        }
    if action == 'fix_session':
        phone = request.GET.get('phone', '5493515999981')
        try:
            session = WhatsAppSession.objects.get(phone_number=phone)
            user = User.objects.get(dni=request.GET.get('dni', '43813147'))
            session.user = user
            session.session_data.pop('awaiting_dni', None)
            session.current_flow = ''
            session.current_step = 0
            session.save(update_fields=['user', 'session_data', 'current_flow', 'current_step', 'last_activity'])
            info['fix_result'] = 'ok'
        except Exception as e:
            info['fix_result'] = str(e)
    if phone:
        sessions = WhatsAppSession.objects.filter(phone_number__contains=phone)
    else:
        sessions = WhatsAppSession.objects.all()[:5]
    for s in sessions:
        info['sessions'].append({
            'phone': s.phone_number,
            'user_id': s.user_id,
            'current_flow': s.current_flow,
            'current_step': s.current_step,
            'session_data': s.session_data,
            'last_activity': str(s.last_activity),
        })
    with connection.cursor() as cursor:
        cursor.execute("SELECT id, username, first_name, dni, telefono FROM users_user ORDER BY id")
        for row in cursor.fetchall():
            info['users'].append({
                'id': row[0], 'username': row[1], 'first_name': row[2],
                'dni': row[3], 'telefono': row[4],
            })
    return JsonResponse(info)

urlpatterns += [
    path('health/', _health, name='chatbot_health'),
    path('debug/', _debug, name='debug'),
]

