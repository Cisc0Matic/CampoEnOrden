import base64
import json
import logging

import anthropic
from django.conf import settings

logger = logging.getLogger(__name__)

_MODEL = 'claude-sonnet-4-6'

_MONITOR_PROMPT = """Analiza esta foto del monitor de una cosechadora agrícola.
Extrae los datos que puedas leer en formato JSON exacto:
{
  "kg_seco": <número o null>,
  "kg_humedo": <número o null>,
  "humedad_pct": <número o null>,
  "hectareas": <número o null>,
  "total_kg": <número o null>,
  "rinde_ha": <número kg/ha o null>
}
Devuelve SOLO el JSON sin explicaciones. Si no puedes leer un valor, usa null."""

_FACTURA_PROMPT = """Analiza esta factura o remito.
Extrae los datos en formato JSON exacto:
{
  "fecha": "<DD/MM/AAAA o null>",
  "proveedor": "<nombre o null>",
  "cuit": "<número o null>",
  "litros": <número o null>,
  "precio_litro": <número o null>,
  "total": <número o null>,
  "nro_documento": "<número o null>",
  "descripcion": "<texto breve o null>"
}
Devuelve SOLO el JSON sin explicaciones."""

_MANTENIMIENTO_PROMPT = """Analiza esta factura de taller o servicio técnico.
Extrae los datos en formato JSON exacto:
{
  "fecha": "<DD/MM/AAAA o null>",
  "taller": "<nombre o null>",
  "cuit": "<número o null>",
  "descripcion": "<descripción de la tarea o null>",
  "repuestos": "<repuestos usados o null>",
  "mano_de_obra": <monto número o null>,
  "total": <número o null>,
  "nro_factura": "<número o null>"
}
Devuelve SOLO el JSON sin explicaciones."""


def _parse_json_response(text: str) -> dict:
    text = text.strip()
    if text.startswith('```'):
        lines = text.split('\n')
        text = '\n'.join(lines[1:-1] if lines[-1] == '```' else lines[1:])
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {}


def _image_content(file_bytes: bytes, mime_type: str) -> dict:
    return {
        'type': 'image',
        'source': {
            'type': 'base64',
            'media_type': mime_type,
            'data': base64.standard_b64encode(file_bytes).decode(),
        },
    }


def _pdf_content(file_bytes: bytes) -> dict:
    return {
        'type': 'document',
        'source': {
            'type': 'base64',
            'media_type': 'application/pdf',
            'data': base64.standard_b64encode(file_bytes).decode(),
        },
    }


class ClaudeVisionService:
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    def _ask(self, media_content: dict, prompt: str) -> dict:
        try:
            msg = self.client.messages.create(
                model=_MODEL,
                max_tokens=512,
                messages=[{
                    'role': 'user',
                    'content': [media_content, {'type': 'text', 'text': prompt}],
                }],
            )
            return _parse_json_response(msg.content[0].text)
        except Exception as e:
            logger.exception(f'Claude Vision error: {e}')
            return {}

    def analyze_cosecha_monitor(self, file_bytes: bytes, mime_type: str = 'image/jpeg') -> dict:
        content = _image_content(file_bytes, mime_type)
        return self._ask(content, _MONITOR_PROMPT)

    def analyze_factura_combustible(self, file_bytes: bytes, mime_type: str) -> dict:
        if mime_type == 'application/pdf':
            content = _pdf_content(file_bytes)
        else:
            content = _image_content(file_bytes, mime_type)
        return self._ask(content, _FACTURA_PROMPT)

    def analyze_factura_mantenimiento(self, file_bytes: bytes, mime_type: str) -> dict:
        if mime_type == 'application/pdf':
            content = _pdf_content(file_bytes)
        else:
            content = _image_content(file_bytes, mime_type)
        return self._ask(content, _MANTENIMIENTO_PROMPT)
