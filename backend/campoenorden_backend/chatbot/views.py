import json
import logging
import re

from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from .models import WhatsAppSession, WhatsAppMessage
from .services.whatsapp import WhatsAppService
from .router import handle_message_router
from users.models import User

_MENU_RE = re.compile(r'\*?MENU\*?', re.IGNORECASE)

logger = logging.getLogger(__name__)


def _normalize_phone(phone: str) -> str:
    return ''.join(c for c in phone if c.isdigit())


def _not_registered_response() -> dict:
    return {
        'body': (
            'Tu número no está registrado en Campo en Orden.\n\n'
            'Si ya tenés acceso, ingresá tu DNI para identificarte:'
        ),
        'buttons': [
            {'type': 'reply', 'reply': {'id': 'REINTENTAR', 'title': '🔄 Volver a intentar'}},
        ],
    }


def _link_telefono(session, user) -> str:
    """Guarda el número de WhatsApp en el perfil del usuario (para que el chatbot
    lo reconozca por número en próximos mensajes). No pisa el número si ya
    pertenece a otro usuario activo."""
    phone = _normalize_phone(session.phone_number or '')
    if not phone or not user or user.telefono:
        return ''
    for u in User.objects.filter(is_active=True).exclude(pk=user.pk).exclude(telefono__isnull=True).exclude(telefono=''):
        up = _normalize_phone(u.telefono)
        if up == phone or (len(up) >= 10 and len(phone) >= 10 and up[-10:] == phone[-10:]):
            return ''
    user.telefono = session.phone_number
    user.save(update_fields=['telefono'])
    return '✅ Tu número de WhatsApp quedó vinculado a tu cuenta.\n\n'


def _handle_dni_fallback(session, text: str) -> dict:
    upper = (text or '').strip().upper()

    # Reintentar / keywords → re-check phone in case the user was just registered
    if upper in ('REINTENTAR', 'GO_MENU', 'MENU', 'HOLA', 'INICIO', 'START', '/START', 'CANCELAR', ''):
        user = _find_user(session.phone_number)
        if user:
            session.user = user
            session.session_data.pop('awaiting_dni', None)
            session.save(update_fields=['user', 'session_data', 'last_activity'])
            from .flows.menu import show_main_menu
            return show_main_menu(user, session)
        return _not_registered_response()

    # Treat input as DNI
    dni = text.strip()
    user = User.objects.filter(dni=dni, is_active=True).first()
    if not user:
        return {
            'body': (
                f'DNI *{dni}* no encontrado en el sistema.\n\n'
                'Verificá el número o contactá a tu asesor.\n\n'
                'Ingresá tu DNI:'
            ),
            'buttons': [
                {'type': 'reply', 'reply': {'id': 'REINTENTAR', 'title': '🔄 Volver a intentar'}},
            ],
        }

    session.user = user
    session.session_data.pop('awaiting_dni', None)
    session.save(update_fields=['user', 'session_data', 'last_activity'])
    from .flows.menu import show_main_menu
    ack = _link_telefono(session, user)
    menu = show_main_menu(user, session)
    if isinstance(menu, dict):
        menu['body'] = ack + menu['body'] if ack else menu['body']
    elif isinstance(menu, str):
        menu = ack + menu if ack else menu
    return menu


def _normalize_reply_phone(phone: str) -> str:
    """Argentina móvil: WhatsApp envía 549XXXXXXXXXX (13 dígitos). Meta espera el formato
    con 15 (ej: 5435115XXXXXXX)."""
    import re
    m = re.match(r'^54(9)(\d{2,4})(\d{7,8})$', phone)
    if m:
        return '54' + m.group(2) + '15' + m.group(3)
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

        for entry in data.get('entry', []):
            for change in entry.get('changes', []):
                value = change.get('value', {})
                for msg in value.get('messages', []):
                    try:
                        self._process_message(msg)
                    except Exception as e:
                        logger.exception(f'Error processing msg {msg.get("id","?")}: {e}')

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
        elif msg_type == 'interactive':
            interactive = msg.get('interactive', {})
            list_reply = interactive.get('list_reply', {})
            button_reply = interactive.get('button_reply', {})
            text = list_reply.get('id', button_reply.get('id', '')).strip()
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

        try:
            session, _ = WhatsAppSession.objects.get_or_create(phone_number=phone)
        except Exception as e:
            logger.exception(f'Error getting/creating session for {phone}: {e}')
            return

        try:
            WhatsAppMessage.objects.create(
                session=session,
                direction=WhatsAppMessage.DIRECTION_IN,
                message_type=msg_type,
                content=text,
                media_id=media_id,
                whatsapp_message_id=message_id,
            )
        except Exception as e:
            logger.exception(f'Error saving incoming msg {message_id}: {e}')

        wa = WhatsAppService()
        if message_id:
            try:
                wa.mark_as_read(message_id)
            except Exception:
                pass

        if not session.user:
            if session.session_data.get('awaiting_dni'):
                response = _handle_dni_fallback(session, text)
            else:
                user = _find_user(phone)
                if user:
                    session.user = user
                    session.save(update_fields=['user', 'last_activity'])
                    _link_telefono(session, user)
                    response = handle_message_router(session, text, media_id, mime_type, wa)
                else:
                    session.session_data['awaiting_dni'] = True
                    session.save(update_fields=['session_data', 'last_activity'])
                    response = _not_registered_response()
        else:
            response = handle_message_router(session, text, media_id, mime_type, wa)

        if response:
            reply_phone = _normalize_reply_phone(phone)
            if isinstance(response, dict):
                if response.get('sections'):
                    wa.send_interactive_list(
                        reply_phone,
                        body=response.get('body', ''),
                        sections=response['sections'],
                        header=response.get('header', ''),
                        footer=response.get('footer', ''),
                        button_text=response.get('button_text', 'Ver opciones'),
                    )
                elif response.get('buttons'):
                    wa.send_reply_buttons(
                        reply_phone,
                        body=response.get('body', ''),
                        buttons=response['buttons'],
                        header=response.get('header', ''),
                        footer=response.get('footer', ''),
                    )
                else:
                    text_response = str(response)
                    wa.send_text(reply_phone, text_response)
                try:
                    WhatsAppMessage.objects.create(
                        session=session,
                        direction=WhatsAppMessage.DIRECTION_OUT,
                        message_type='interactive',
                        content=response.get('body', ''),
                    )
                except Exception:
                    pass
            else:
                text_response = response if isinstance(response, str) else str(response)
                if _MENU_RE.search(text_response):
                    clean = _MENU_RE.sub('').replace('  ', ' ').replace('\n\n\n', '\n\n').strip()
                    wa.send_reply_buttons(clean.rstrip('.'), [
                        {'type': 'reply', 'reply': {'id': 'GO_MENU', 'title': '📋 Menú principal'}},
                    ])
                else:
                    wa.send_text(reply_phone, text_response)
                try:
                    WhatsAppMessage.objects.create(
                        session=session,
                        direction=WhatsAppMessage.DIRECTION_OUT,
                        message_type='text',
                        content=text_response,
                    )
                except Exception:
                    pass
