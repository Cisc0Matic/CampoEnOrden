"""
Endpoint de simulacion local del chatbot. Solo disponible en DEBUG=True.
Uso:
  POST /api/chatbot/sim/
  {"phone": "5491112345678", "text": "1"}
  {"phone": "5491112345678", "media_id": "fake_id", "mime_type": "image/jpeg"}
"""
import json

from django.conf import settings
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from .models import WhatsAppSession, WhatsAppMessage
from .router import handle_message_router
from users.models import User


def _normalize_phone(phone: str) -> str:
    return ''.join(c for c in phone if c.isdigit())


def _find_user(phone: str):
    normalized = _normalize_phone(phone)
    for user in User.objects.filter(is_active=True).exclude(telefono__isnull=True).exclude(telefono=''):
        user_phone = _normalize_phone(user.telefono)
        if user_phone == normalized:
            return user
        if len(normalized) >= 10 and len(user_phone) >= 10:
            if user_phone[-10:] == normalized[-10:]:
                return user
    return None


@method_decorator(csrf_exempt, name='dispatch')
class SimulatorView(View):

    def get(self, request):
        if not settings.DEBUG:
            return JsonResponse({'error': 'Solo disponible en DEBUG'}, status=403)

        phone = request.GET.get('phone', '')
        if not phone:
            return JsonResponse({
                'info': 'Simulador de chatbot Campo en Orden',
                'uso': 'POST /api/chatbot/sim/ con {"phone": "...", "text": "..."}',
                'usuarios': list(User.objects.filter(is_active=True).values('id', 'username', 'role', 'telefono')),
                'sesiones': list(WhatsAppSession.objects.values('phone_number', 'current_flow', 'current_step', 'last_activity')),
            })

        session = WhatsAppSession.objects.filter(phone_number=phone).first()
        history = []
        if session:
            history = list(session.messages.order_by('-timestamp').values('direction', 'message_type', 'content')[:20])
            history.reverse()
        return JsonResponse({
            'phone': phone,
            'session': {
                'flow': session.current_flow if session else None,
                'step': session.current_step if session else None,
                'data': session.session_data if session else {},
            },
            'history': history,
        })

    def post(self, request):
        if not settings.DEBUG:
            return JsonResponse({'error': 'Solo disponible en DEBUG'}, status=403)

        try:
            body = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'JSON invalido'}, status=400)

        phone = body.get('phone', '').strip()
        text = body.get('text', '').strip()
        media_id = body.get('media_id', '')
        mime_type = body.get('mime_type', 'image/jpeg')

        if not phone:
            return JsonResponse({'error': 'phone es requerido'}, status=400)

        user = _find_user(phone)
        session, created = WhatsAppSession.objects.get_or_create(
            phone_number=phone,
            defaults={'user': user},
        )
        if user and session.user_id != (user.pk if user else None):
            session.user = user
            session.save(update_fields=['user'])

        if text or media_id:
            WhatsAppMessage.objects.create(
                session=session,
                direction=WhatsAppMessage.DIRECTION_IN,
                message_type='image' if media_id else 'text',
                content=text,
                media_id=media_id,
            )

        if not user:
            response = (
                'Tu numero no esta registrado en Campo en Orden. '
                'Contacta a tu asesor para que te habilite el acceso.'
            )
        else:
            # Wrap WhatsAppService to avoid real API calls in simulation
            wa = _FakeWhatsAppService()
            response = handle_message_router(session, text, media_id, mime_type, wa)

        if response:
            WhatsAppMessage.objects.create(
                session=session,
                direction=WhatsAppMessage.DIRECTION_OUT,
                message_type='text',
                content=response,
            )

        session.refresh_from_db()
        return JsonResponse({
            'response': response,
            'session': {
                'flow': session.current_flow,
                'step': session.current_step,
                'data': session.session_data,
            },
            'user': user.username if user else None,
        })

    def delete(self, request):
        """Reset session for a phone number."""
        if not settings.DEBUG:
            return JsonResponse({'error': 'Solo disponible en DEBUG'}, status=403)
        try:
            body = json.loads(request.body)
            phone = body.get('phone', '')
        except Exception:
            phone = request.GET.get('phone', '')
        if phone:
            WhatsAppSession.objects.filter(phone_number=phone).delete()
            return JsonResponse({'reset': True, 'phone': phone})
        return JsonResponse({'error': 'phone requerido'}, status=400)


class _FakeWhatsAppService:
    """Mock WhatsApp service for local simulation — no real API calls."""
    def send_text(self, to, text):
        return {}

    def send_interactive_list(self, to, body, sections, header='', footer='', button_text='Ver opciones'):
        return {}

    def send_reply_buttons(self, to, body, buttons, header='', footer=''):
        return {}

    def get_media_url(self, media_id):
        return ''

    def download_media(self, url):
        return b''

    def mark_as_read(self, msg_id):
        pass
