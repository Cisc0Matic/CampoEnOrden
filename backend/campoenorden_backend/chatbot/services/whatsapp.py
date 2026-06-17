import hashlib
import hmac
import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

_API_VERSION = 'v21.0'
_GRAPH_BASE = f'https://graph.facebook.com/{_API_VERSION}'


class WhatsAppService:
    def __init__(self):
        self.access_token = getattr(settings, 'WHATSAPP_ACCESS_TOKEN', '')
        self.phone_number_id = getattr(settings, 'WHATSAPP_PHONE_NUMBER_ID', '')
        self._app_secret = getattr(settings, 'WHATSAPP_APP_SECRET', '')

    def _headers(self) -> dict:
        return {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json',
        }

    def _proof(self) -> str:
        """HMAC-SHA256(app_secret, access_token) — requerido por Meta para llamadas servidor-a-servidor."""
        return hmac.new(
            self._app_secret.encode(), self.access_token.encode(), hashlib.sha256
        ).hexdigest()

    def send_text(self, to: str, text: str) -> dict:
        url = f'{_GRAPH_BASE}/{self.phone_number_id}/messages'
        payload = {
            'messaging_product': 'whatsapp',
            'recipient_type': 'individual',
            'to': to,
            'type': 'text',
            'text': {'body': text, 'preview_url': False},
        }
        try:
            resp = requests.post(
                url, json=payload, headers=self._headers(),
                params={'appsecret_proof': self._proof()} if self._app_secret else {},
                timeout=15,
            )
            data = resp.json()
            if 'error' in data:
                logger.error(f'WhatsApp send_text API error: {data["error"]}')
            return data
        except Exception as e:
            logger.exception(f'WhatsApp send_text error: {e}')
            return {}

    def get_media_url(self, media_id: str) -> str:
        url = f'{_GRAPH_BASE}/{media_id}'
        params = {'appsecret_proof': self._proof()} if self._app_secret else {}
        try:
            resp = requests.get(
                url,
                headers={'Authorization': f'Bearer {self.access_token}'},
                params=params,
                timeout=10,
            )
            return resp.json().get('url', '')
        except Exception as e:
            logger.exception(f'WhatsApp get_media_url error: {e}')
            return ''

    def download_media(self, media_url: str) -> bytes:
        try:
            resp = requests.get(
                media_url,
                headers={'Authorization': f'Bearer {self.access_token}'},
                timeout=60,
            )
            return resp.content
        except Exception as e:
            logger.exception(f'WhatsApp download_media error: {e}')
            return b''

    def mark_as_read(self, message_id: str) -> None:
        url = f'{_GRAPH_BASE}/{self.phone_number_id}/messages'
        payload = {
            'messaging_product': 'whatsapp',
            'status': 'read',
            'message_id': message_id,
        }
        try:
            requests.post(
                url, json=payload, headers=self._headers(),
                params={'appsecret_proof': self._proof()} if self._app_secret else {},
                timeout=5,
            )
        except Exception:
            pass

    @staticmethod
    def verify_signature(payload: bytes, signature_header: str) -> bool:
        app_secret = getattr(settings, 'WHATSAPP_APP_SECRET', '')
        if not app_secret:
            return True
        try:
            expected = 'sha256=' + hmac.new(
                app_secret.encode(), payload, hashlib.sha256
            ).hexdigest()
            return hmac.compare_digest(expected, signature_header)
        except Exception:
            return False
