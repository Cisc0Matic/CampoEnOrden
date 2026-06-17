import json
import logging

from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from .models import WhatsAppSession, WhatsAppMessage
from .services.whatsapp import WhatsAppService
from .router import handle_message_router
from users.models import User

logger = logging.getLogger(__name__)


def _normalize_phone(phone: str) -> str:
    return ''.join(c for c in phone if c.isdigit())


def _normalize_reply_phone(phone: str) -> str:
    """Argentina móvil: WhatsApp usa 549XXXXXXXXXX (13 dígitos) pero la API acepta 54XXXXXXXXXX (12 dígitos).
    En cuentas de prueba el whitelist suele tener el formato sin el 9 extra."""
    import re
    if re.match(r'^549\d{10}$', phone):
        return '54' + phone[3:]
    return phone


def _find_user(phone: str):
    normalized = _normalize_phone(phone)
    for user in User.objects.filter(is_active=True).exclude(telefono__isnull=True).exclude(telefono=''):
        user_phone = _normalize_phone(user.telefono)
        if user_phone == normalized:
            return user
        # Match last 10 digits (handles country code differences)
        if len(normalized) >= 10 and len(user_phone) >= 10:
            if user_phone[-10:] == normalized[-10:]:
                return user
    return None


@method_decorator(csrf_exempt, name='dispatch')
class WhatsAppWebhookView(View):

    def get(self, request):
        """Meta webhook verification."""
        mode = request.GET.get('hub.mode')
        token = request.GET.get('hub.verify_token')
        challenge = request.GET.get('hub.challenge')
        if mode == 'subscribe' and token == getattr(settings, 'WHATSAPP_WEBHOOK_VERIFY_TOKEN', ''):
            return HttpResponse(challenge, content_type='text/plain')
        return HttpResponse(status=403)

    def post(self, request):
        """Process incoming WhatsApp messages."""
        # Signature verification
        signature = request.headers.get('X-Hub-Signature-256', '')
        if not WhatsAppService.verify_signature(request.body, signature):
            logger.warning('WhatsApp webhook signature mismatch')
            return HttpResponse(status=403)

        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return HttpResponse(status=400)

        try:
            for entry in data.get('entry', []):
                for change in entry.get('changes', []):
                    value = change.get('value', {})
                    for msg in value.get('messages', []):
                        self._process_message(msg)
        except Exception as e:
            logger.exception(f'Webhook processing error: {e}')

        # Always return 200 so Meta doesn't retry
        return JsonResponse({'status': 'ok'})

    def _process_message(self, msg: dict) -> None:
        phone = msg.get('from', '')
        message_id = msg.get('id', '')
        msg_type = msg.get('type', 'text')

        # Skip already-processed messages
        if message_id and WhatsAppMessage.objects.filter(whatsapp_message_id=message_id).exists():
            return

        text, media_id, mime_type = '', '', ''

        if msg_type == 'text':
            text = msg.get('text', {}).get('body', '').strip()
        elif msg_type == 'image':
            media_id = msg.get('image', {}).get('id', '')
            mime_type = msg.get('image', {}).get('mime_type', 'image/jpeg')
            text = msg.get('image', {}).get('caption', '').strip()
        elif msg_type == 'document':
            media_id = msg.get('document', {}).get('id', '')
            mime_type = msg.get('document', {}).get('mime_type', 'application/pdf')
            text = msg.get('document', {}).get('caption', '').strip()
        elif msg_type in ('audio', 'video', 'sticker', 'location', 'contacts', 'reaction'):
            return  # Not handled

        if not phone:
            return

        session, _ = WhatsAppSession.objects.get_or_create(phone_number=phone)

        WhatsAppMessage.objects.create(
            session=session,
            direction=WhatsAppMessage.DIRECTION_IN,
            message_type=msg_type,
            content=text,
            media_id=media_id,
            whatsapp_message_id=message_id,
        )

        wa = WhatsAppService()
        if message_id:
            wa.mark_as_read(message_id)

        if not session.user:
            session.session_data['awaiting_dni'] = True
            session.save(update_fields=['session_data', 'last_activity'])
            response = (
                'Bienvenido a Campo en Orden.\n'
                'Por favor, ingresá tu DNI para identificarte:'
            )
        else:
            response = handle_message_router(session, text, media_id, mime_type, wa)

        if response:
            wa.send_text(_normalize_reply_phone(phone), response)
            WhatsAppMessage.objects.create(
                session=session,
                direction=WhatsAppMessage.DIRECTION_OUT,
                message_type='text',
                content=response,
            )
