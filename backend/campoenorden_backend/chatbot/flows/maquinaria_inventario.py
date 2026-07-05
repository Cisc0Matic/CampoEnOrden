import logging
from datetime import date

from .base import BaseFlow

logger = logging.getLogger(__name__)

_TIPO_MAP = {
    '1': 'TRACTOR',
    '2': 'COSECHADORA',
    '3': 'PULVERIZADORA',
    '4': 'SEMBRADORA',
    '5': 'CAMION',
    '6': 'CAMIONETA',
    '7': 'DRONE',
    '8': 'AVION',
    '9': 'OTRO',
}
_TIPO_DISPLAY = {
    'TRACTOR': 'Tractor',
    'COSECHADORA': 'Cosechadora',
    'PULVERIZADORA': 'Pulverizadora',
    'SEMBRADORA': 'Sembradora',
    'CAMION': 'Camión',
    'CAMIONETA': 'Camioneta',
    'DRONE': 'Drone',
    'AVION': 'Avión fumigador',
    'OTRO': 'Otro',
}
_SEGURO_ALERT_DAYS = 7


class MaquinariaInventarioFlow(BaseFlow):
    FLOW_NAME = 'maquinaria_inventario'

    # 0: show options (ver / alta)
    def step_0(self, message, media_id, mime_type):
        return self._reply_buttons(
            '*Inventario de Maquinaria*\n¿Qué querés hacer?',
            [
                {'type': 'reply', 'reply': {'id': '1', 'title': '📋 Ver inventario'}},
                {'type': 'reply', 'reply': {'id': '2', 'title': '➕ Dar de alta'}},
                {'type': 'reply', 'reply': {'id': 'GO_MENU', 'title': '📋 Menú'}},
            ],
        )

    # 1: process option
    def step_1(self, message, media_id, mime_type):
        opt = self._parse_int(message, 1, 2)
        if opt == 1:
            return self._show_inventario()
        if opt == 2:
            self._advance_to(2)
            return self._reply_buttons(
                '¿Cómo querés cargar los datos?',
                [
                    {'type': 'reply', 'reply': {'id': '1', 'title': '📷 Foto/PDF del título'}},
                    {'type': 'reply', 'reply': {'id': '2', 'title': '✍️ Carga manual'}},
                    {'type': 'reply', 'reply': {'id': 'GO_MENU', 'title': '📋 Menú'}},
                ],
            )
        return self._invalid(2)

    # 2: choose foto / manual
    def step_2(self, message, media_id, mime_type):
        opt = self._parse_int(message, 1, 2)
        if opt == 1:
            self.data['modo'] = 'FOTO'
            self._advance_to(3)
            return (
                'Enviá la foto o PDF del título de la máquina.\n\n'
                'Claude va a extraer los datos automáticamente.'
            )
        if opt == 2:
            self.data['modo'] = 'MANUAL'
            self._advance_to(10)
            return self._tipo_list()
        return self._invalid(2)

    # 3: receive image → run vision
    def step_3(self, message, media_id, mime_type):
        if not media_id:
            return 'Por favor enviá la foto o PDF del título de la máquina.'
        extracted = self._run_vision_titulo(media_id, mime_type)
        self.data['vision_data'] = extracted
        self._advance_to(4)
        if extracted:
            tipo_d = _TIPO_DISPLAY.get(extracted.get('tipo', ''), extracted.get('tipo', '?'))
            return self._confirm_buttons(
                '📋 *Datos extraídos del título:*\n\n'
                f"Tipo: {tipo_d}\n"
                f"Marca: {extracted.get('marca') or '?'}\n"
                f"Modelo: {extracted.get('modelo') or '?'}\n"
                f"Año: {extracted.get('ano') or '?'}\n"
                f"Dominio: {extracted.get('dominio') or '?'}\n"
                f"N° serie: {extracted.get('nro_serie') or '?'}\n"
                f"Titular: {extracted.get('titular') or '?'}"
            )
        return self._reply_buttons(
            'No pude leer el título automáticamente.',
            [
                {'type': 'reply', 'reply': {'id': '1', 'title': '📷 Otra foto/PDF'}},
                {'type': 'reply', 'reply': {'id': '2', 'title': '✍️ Carga manual'}},
                {'type': 'reply', 'reply': {'id': 'GO_MENU', 'title': '📋 Menú'}},
            ],
        )

    # 4: confirm/correct vision (or retry/manual when vision failed)
    def step_4(self, message, media_id, mime_type):
        vision_ok = bool(self.data.get('vision_data'))
        opt = self._parse_int(message, 1, 2)

        if not vision_ok:
            if opt == 1:
                self._advance_to(3)
                return 'Enviá otra foto o PDF del título.'
            if opt == 2:
                self.data['modo'] = 'MANUAL'
                self._advance_to(10)
                return self._tipo_list()
            return self._invalid(2)

        # Vision succeeded: opt 1=confirm, opt 2=correct (CANCELAR handled by handle())
        if opt == 1:
            v = self.data['vision_data']
            self.data.update({
                'tipo': v.get('tipo') or 'OTRO',
                'marca': v.get('marca') or '',
                'modelo': v.get('modelo') or '',
                'ano': v.get('ano'),
                'dominio': v.get('dominio') or '',
                'nro_serie': v.get('nro_serie') or '',
                'hp': v.get('hp'),
            })
            self._advance_to(5)
            return self._propietario_buttons()
        if opt == 2:
            self.data['modo'] = 'MANUAL'
            self._advance_to(10)
            return self._tipo_list()
        return self._invalid(2)

    # 5: propietario (convergence: both foto-confirmed and manual paths arrive here)
    def step_5(self, message, media_id, mime_type):
        opt = self._parse_int(message, 1, 2)
        if opt is None:
            return self._propietario_buttons()
        self.data['propietario'] = 'PROPIA' if opt == 1 else 'CONTRATISTA'
        self._advance_to(6)
        return 'Precio de mercado en USD (número o - para omitir):\nEj: 85000'

    # 6: precio mercado USD
    def step_6(self, message, media_id, mime_type):
        val = message.strip()
        if val == '-':
            self.data['precio_mercado_usd'] = None
        else:
            n = self._parse_float(val)
            if n is None:
                return 'Ingresá un número válido o - para omitir.'
            self.data['precio_mercado_usd'] = n
        self._advance_to(7)
        return 'Vencimiento del seguro (DD/MM/AA o - para omitir):'

    # 7: vencimiento seguro
    def step_7(self, message, media_id, mime_type):
        val = message.strip()
        if val == '-':
            self.data['vencimiento_seguro'] = None
        else:
            fecha = self._parse_date(val)
            if not fecha:
                return 'Formato incorrecto. Usá DD/MM/AA o - para omitir.'
            self.data['vencimiento_seguro'] = fecha.isoformat()
        self._advance_to(8)
        return self._build_confirmation()

    # 8: final confirmation
    def step_8(self, message, media_id, mime_type):
        opt = self._parse_int(message, 1, 3)
        if opt == 1:
            return self._confirm_save()
        if opt == 2:
            self._restart_flow()
            return self.step_0('', None, None)
        return self._cancel()

    # ── Manual entry steps (10–16) ────────────────────────────────────────────

    def step_10(self, message, media_id, mime_type):
        tipo = _TIPO_MAP.get(message.strip())
        if not tipo:
            return self._tipo_list()
        self.data['tipo'] = tipo
        self._advance_to(11)
        return 'Marca:\nEj: New Holland'

    def step_11(self, message, media_id, mime_type):
        self.data['marca'] = message.strip()
        self._advance_to(12)
        return 'Modelo:\nEj: T7.210'

    def step_12(self, message, media_id, mime_type):
        self.data['modelo'] = message.strip()
        self._advance_to(13)
        return 'Año (número):\nEj: 2023'

    def step_13(self, message, media_id, mime_type):
        try:
            ano = int(message.strip())
            if not 1900 <= ano <= 2100:
                raise ValueError
            self.data['ano'] = ano
        except ValueError:
            return 'Ingresá un año válido. Ej: 2023'
        self._advance_to(14)
        return 'Dominio / patente (o - para omitir):\nEj: AB123BC'

    def step_14(self, message, media_id, mime_type):
        val = message.strip()
        self.data['dominio'] = '' if val == '-' else val
        self._advance_to(15)
        return 'N° de serie (o - para omitir):'

    def step_15(self, message, media_id, mime_type):
        val = message.strip()
        self.data['nro_serie'] = '' if val == '-' else val
        self._advance_to(16)
        return 'HP / potencia (número o - para omitir):\nEj: 210'

    def step_16(self, message, media_id, mime_type):
        val = message.strip()
        if val == '-':
            self.data['hp'] = None
        else:
            try:
                self.data['hp'] = int(val)
            except ValueError:
                return 'Ingresá un número entero o - para omitir.'
        # Converge with foto path
        self._advance_to(5)
        return self._propietario_buttons()

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _tipo_list(self) -> dict:
        rows = [{'id': k, 'title': _TIPO_DISPLAY[v]} for k, v in _TIPO_MAP.items()]
        return self._interactive_list(
            'Tipo de máquina:',
            [{'title': 'Tipo', 'rows': rows}],
        )

    def _propietario_buttons(self) -> dict:
        return self._reply_buttons(
            '¿La máquina es propia o de un contratista?',
            [
                {'type': 'reply', 'reply': {'id': '1', 'title': 'Propia'}},
                {'type': 'reply', 'reply': {'id': '2', 'title': 'Contratista'}},
                {'type': 'reply', 'reply': {'id': 'GO_MENU', 'title': '📋 Menú'}},
            ],
        )

    def _show_inventario(self) -> dict:
        from chatbot.models import Maquinaria
        from chatbot.flows.menu import get_maquinaria_submenu
        maquinas = list(Maquinaria.objects.filter(activo=True).order_by('tipo', 'marca', 'modelo'))
        if not maquinas:
            return self._finish_with_submenu(
                'No hay maquinaria registrada en el inventario.\n\n'
                'Usá "Dar de alta" para agregar tu primera máquina.',
                get_maquinaria_submenu,
            )
        today = date.today()
        lines = ['⚙️ *Inventario de Maquinaria*\n']
        for m in maquinas:
            tipo_d = _TIPO_DISPLAY.get(m.tipo, m.tipo)
            partes = [f'• *{tipo_d}*']
            if m.marca or m.modelo:
                partes.append(f'{m.marca} {m.modelo}'.strip())
            if m.ano:
                partes.append(f'({m.ano})')
            if m.dominio:
                partes.append(f'— {m.dominio}')
            if m.propietario == 'CONTRATISTA':
                partes.append('🔧')
            if m.precio_mercado_usd:
                partes.append(f'u$s {m.precio_mercado_usd:,.0f}')
            linea = ' '.join(partes)
            if m.vencimiento_seguro:
                dias = (m.vencimiento_seguro - today).days
                if dias < 0:
                    linea += f'\n  ⚠️ *SEGURO VENCIDO* ({m.vencimiento_seguro})'
                elif dias <= _SEGURO_ALERT_DAYS:
                    linea += f'\n  ⚠️ Seguro vence en {dias} días ({m.vencimiento_seguro})'
            lines.append(linea)
        return self._finish_with_submenu('\n'.join(lines), get_maquinaria_submenu)

    def _build_confirmation(self) -> dict:
        d = self.data
        tipo_d = _TIPO_DISPLAY.get(d.get('tipo', ''), d.get('tipo', '-'))
        prop_d = 'Propia' if d.get('propietario') == 'PROPIA' else 'Contratista'
        rows = [
            ('Tipo', tipo_d),
            ('Marca', d.get('marca') or '-'),
            ('Modelo', d.get('modelo') or '-'),
            ('Año', str(d['ano']) if d.get('ano') else '-'),
            ('Dominio', d.get('dominio') or '-'),
            ('N° serie', d.get('nro_serie') or '-'),
            ('HP', str(d['hp']) if d.get('hp') else '-'),
            ('Propietario', prop_d),
        ]
        if d.get('precio_mercado_usd'):
            rows.append(('Precio mercado', f"u$s {d['precio_mercado_usd']:,.0f}"))
        if d.get('vencimiento_seguro'):
            rows.append(('Venc. seguro', d['vencimiento_seguro']))
        return self._confirmation_block('Confirmar alta de máquina', rows)

    def _confirm_save(self) -> dict:
        d = self.data
        from chatbot.models import Maquinaria
        from chatbot.flows.menu import get_maquinaria_submenu
        try:
            nombre = f"{d.get('marca', '')} {d.get('modelo', '')}".strip() or 'Sin nombre'
            m = Maquinaria.objects.create(
                nombre=nombre,
                tipo=d.get('tipo', 'OTRO'),
                marca=d.get('marca', ''),
                modelo=d.get('modelo', ''),
                ano=d.get('ano'),
                dominio=d.get('dominio', ''),
                hp=d.get('hp'),
                propietario=d.get('propietario', 'PROPIA'),
                precio_mercado_usd=d.get('precio_mercado_usd'),
                vencimiento_seguro=d.get('vencimiento_seguro'),
            )
        except Exception as e:
            logger.exception(f'Error saving maquinaria: {e}')
            return self._with_menu('Error al guardar. Intentá de nuevo.')
        tipo_d = _TIPO_DISPLAY.get(m.tipo, m.tipo)
        return self._finish_with_submenu(
            f'✅ *{tipo_d} {m.nombre}* registrado en el inventario.',
            get_maquinaria_submenu,
        )

    def _run_vision_titulo(self, media_id: str, mime_type: str) -> dict:
        try:
            from chatbot.services.whatsapp import WhatsAppService
            from chatbot.services.claude_vision import ClaudeVisionService
            wa = WhatsAppService()
            url = wa.get_media_url(media_id)
            if not url:
                return {}
            data = wa.download_media(url)
            if not data:
                return {}
            return ClaudeVisionService().analyze_titulo_maquinaria(data, mime_type or 'image/jpeg')
        except Exception as e:
            logger.exception(f'Vision titulo error: {e}')
            return {}
