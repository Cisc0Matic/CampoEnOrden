import logging
import re
from datetime import date, datetime

logger = logging.getLogger(__name__)

CULTIVOS_LIST = ['Trigo', 'Soja 1', 'Soja 2', 'Maiz', 'Girasol', 'Sorgo', 'Mani', 'CS']
_CULTIVOS_ROWS = [{'id': str(i+1), 'title': c} for i, c in enumerate(CULTIVOS_LIST)]


def parse_product(text: str) -> dict:
    parts = [p.strip() for p in text.rsplit(' - ', 2)]
    if len(parts) < 2:
        raise ValueError('Formato incorrecto')
    nombre = parts[0]
    dosis_str = parts[1] if len(parts) > 1 else ''
    total_str = parts[2] if len(parts) > 2 else ''

    def extract_num(s):
        m = re.search(r'[\d]+[,.]?[\d]*', s)
        return float(m.group().replace(',', '.')) if m else None

    def extract_unit(s):
        m = re.search(r'[A-Za-z/]+', s)
        return m.group() if m else 'L/ha'

    return {
        'nombre': nombre,
        'dosis': extract_num(dosis_str),
        'dosis_str': dosis_str,
        'total': extract_num(total_str),
        'total_str': total_str,
        'unidad_dosis': extract_unit(dosis_str),
    }


class BaseFlow:
    FLOW_NAME = ''

    def __init__(self, session, wa_service):
        self.session = session
        self.wa = wa_service
        self.phone = session.phone_number
        self.data = dict(session.session_data or {})

    def handle(self, message: str, media_id: str = None, mime_type: str = None):
        upper = (message or '').strip().upper()
        if upper in ('GO_MENU', 'MENU', 'INICIO', '/START'):
            return self._go_to_menu()
        if upper == 'CANCELAR':
            return self._cancel()
        try:
            step = self.session.current_step
            handler = getattr(self, f'step_{step}', None)
            if handler:
                return handler(message or '', media_id, mime_type)
            return self._go_to_menu()
        except Exception as e:
            logger.exception(f'Flow {self.FLOW_NAME} step {self.session.current_step} error: {e}')
            return self._with_menu('Ocurrio un error inesperado.')

    def _advance_to(self, step: int) -> None:
        self.session.current_step = step
        self.session.session_data = self.data
        self.session.save(update_fields=['current_step', 'session_data', 'last_activity'])

    def _save_data(self, **kwargs) -> None:
        self.data.update(kwargs)
        self.session.session_data = self.data
        self.session.save(update_fields=['session_data', 'last_activity'])

    def _go_to_menu(self):
        from chatbot.flows.menu import show_main_menu
        self.session.current_flow = ''
        self.session.current_step = 0
        self.session.session_data = {}
        self.session.save(update_fields=['current_flow', 'current_step', 'session_data', 'last_activity'])
        return show_main_menu(self.session.user)

    def _cancel(self) -> dict:
        self.session.current_flow = ''
        self.session.current_step = 0
        self.session.session_data = {}
        self.session.save(update_fields=['current_flow', 'current_step', 'session_data', 'last_activity'])
        return self._with_menu('Operación cancelada.')

    def _invalid(self, n: int) -> dict:
        return self._with_menu(f'Opción no válida. Seleccioná un número del 1 al {n}.')

    @staticmethod
    def _with_menu(text: str, action_btn: tuple = None) -> dict:
        buttons = [{'type': 'reply', 'reply': {'id': 'GO_MENU', 'title': '📋 Menú principal'}}]
        if action_btn:
            buttons.insert(0, {'type': 'reply', 'reply': {'id': action_btn[0], 'title': action_btn[1]}})
        return {'body': text, 'buttons': buttons}

    def _finish_with_submenu(self, text: str, submenu_fn) -> dict:
        self.session.current_flow = ''
        self.session.current_step = 0
        self.session.session_data = {}
        self.session.save(update_fields=['current_flow', 'current_step', 'session_data', 'last_activity'])
        submenu = submenu_fn()
        submenu['body'] = f'{text}\n\n{submenu["body"]}'
        return submenu

    def _parse_int(self, message: str, min_val: int, max_val: int):
        try:
            v = int((message or '').strip())
            if min_val <= v <= max_val:
                return v
        except (ValueError, TypeError):
            pass
        return None

    def _parse_date(self, message: str):
        if (message or '').strip().upper() == 'HOY':
            return date.today()
        for fmt in ('%d/%m/%y', '%d/%m/%Y'):
            try:
                return datetime.strptime((message or '').strip(), fmt).date()
            except ValueError:
                continue
        return None

    def _parse_float(self, message: str):
        try:
            return float((message or '').strip().replace(',', '.').replace('%', ''))
        except ValueError:
            return None

    # ---- Interactive helpers ----

    def _interactive_list(self, body: str, sections: list[dict],
                           header: str = '', footer: str = '', button_text: str = 'Ver opciones') -> dict:
        result = {'body': body, 'sections': sections, 'button_text': button_text}
        if header:
            result['header'] = header
        if footer:
            result['footer'] = footer
        return result

    def _reply_buttons(self, body: str, buttons: list[dict], header: str = '', footer: str = '') -> dict:
        result = {'body': body, 'buttons': buttons}
        if header:
            result['header'] = header
        if footer:
            result['footer'] = footer
        return result

    def _yes_no_buttons(self, text: str) -> dict:
        return self._reply_buttons(text, [
            {'type': 'reply', 'reply': {'id': '1', 'title': 'Sí'}},
            {'type': 'reply', 'reply': {'id': '2', 'title': 'No'}},
            {'type': 'reply', 'reply': {'id': 'GO_MENU', 'title': '📋 Menú'}},
        ])

    def _who_buttons(self, text: str) -> dict:
        return self._reply_buttons(text, [
            {'type': 'reply', 'reply': {'id': '1', 'title': 'Personal propio'}},
            {'type': 'reply', 'reply': {'id': '2', 'title': 'Contratista'}},
            {'type': 'reply', 'reply': {'id': 'GO_MENU', 'title': '📋 Menú'}},
        ])

    def _confirm_buttons(self, text: str = '') -> dict:
        body = text or '¿Confirmar los datos?'
        return self._reply_buttons(body, [
            {'type': 'reply', 'reply': {'id': '1', 'title': '✅ Confirmar'}},
            {'type': 'reply', 'reply': {'id': '2', 'title': '🔄 Corregir'}},
            {'type': 'reply', 'reply': {'id': 'GO_MENU', 'title': '📋 Menú'}},
        ])

    def _option_list(self, body: str, options: list[tuple], section_title: str = 'Opciones') -> dict:
        rows = [{'id': str(i+1), 'title': title} for i, (_, title) in enumerate(options)]
        return self._interactive_list(body, [{'title': section_title, 'rows': rows}])

    def _cultivo_list(self, body: str = 'Cultivo?') -> dict:
        return self._interactive_list(body, [{'title': 'Cultivos', 'rows': _CULTIVOS_ROWS}])

    # ---- Shared field steps ----

    def _get_campos(self):
        from core.models import Campo
        return list(Campo.objects.all().order_by('nombre'))

    def _step_ask_campo(self):
        campos = self._get_campos()
        if not campos:
            return self._with_menu('No hay campos activos registrados.')
        rows = [{'id': str(i+1), 'title': c.nombre} for i, c in enumerate(campos)]
        self.data = {'campos_ids': [c.id for c in campos]}
        self._advance_to(1)
        return self._interactive_list('¿En qué campo?', [{'title': 'Campos', 'rows': rows}],
                                       header='Seleccionar campo')

    def _get_lotes(self, campo_id):
        from core.models import Lote, Campana
        campania = Campana.objects.filter(activa=True).first()
        if not campania:
            return []
        return list(Lote.objects.filter(campo_id=campo_id, campana=campania).order_by('nombre'))

    def _step_process_campo_ask_lote(self, message: str):
        campos_ids = self.data.get('campos_ids', [])
        n = self._parse_int(message, 1, len(campos_ids))
        if n is None:
            return self._invalid(len(campos_ids))
        from core.models import Campo
        campo = Campo.objects.get(id=campos_ids[n - 1])
        lotes = self._get_lotes(campo.id)
        if not lotes:
            return self._with_menu('No hay lotes registrados en este campo para la campaña activa.')
        rows = [{'id': str(i+1), 'title': f'{l.nombre} ({l.superficie} ha)'} for i, l in enumerate(lotes)]
        self.data.update({'campo_id': campo.id, 'campo_nombre': campo.nombre, 'lotes_ids': [l.id for l in lotes]})
        self._advance_to(2)
        return self._interactive_list('¿En qué lote?', [{'title': 'Lotes', 'rows': rows}],
                                       header='Seleccionar lote')

    def _step_process_lote(self, message: str, next_step: int, next_prompt: str):
        lotes_ids = self.data.get('lotes_ids', [])
        n = self._parse_int(message, 1, len(lotes_ids))
        if n is None:
            return self._invalid(len(lotes_ids))
        from core.models import Lote
        lote = Lote.objects.get(id=lotes_ids[n - 1])
        self.data.update({'lote_id': lote.id, 'lote_nombre': lote.nombre, 'hectareas': float(lote.superficie)})
        self._advance_to(next_step)
        return next_prompt

    def _products_prompt(self, count: int = 0) -> str:
        n = count + 1
        return (
            f'Producto {n} — usá el formato:\n'
            'PRODUCTO - DOSIS/HA - TOTAL\n'
            'Ej: Roundup - 3 L/ha - 15 L\n\n'
            'Cuando termines todos los productos escribí *LISTO*'
        )

    def _products_loop(self, message: str, next_step: int, next_prompt: str) -> str:
        if message.strip().upper() == 'LISTO':
            if not self.data.get('productos'):
                return self._with_menu('Debés cargar al menos un producto antes de continuar.',
                                        action_btn=('LISTO', '🔁 Reintentar'))
            self._advance_to(next_step)
            return next_prompt
        try:
            prod = parse_product(message)
            productos = self.data.get('productos', [])
            productos.append(prod)
            self.data['productos'] = productos
            self._save_data()
            count = len(productos)
            return f'Producto {count} cargado: {prod["nombre"]}.\n\n' + self._products_prompt(count)
        except ValueError:
            return (
                'Formato incorrecto. Usá: PRODUCTO - DOSIS/HA - TOTAL\n'
                'Ej: Roundup - 3 L/ha - 15 L\n\n'
                'O escribí *LISTO* para terminar.'
            )

    def _confirmation_block(self, title: str, rows: list) -> dict:
        lines = [f'*{title}*', '']
        for label, value in rows:
            lines.append(f'*{label}:* {value}')
        body = '\n'.join(lines)
        return self._confirm_buttons(body)

    def _restart_flow(self) -> None:
        self.data = {}
        self.session.current_step = 0
        self.session.session_data = {}
        self.session.save(update_fields=['current_step', 'session_data', 'last_activity'])

    def _save_insumo_usage(self, labor, products: list) -> None:
        from core.models import Insumo, LaborInsumo
        for prod in products:
            nombre = prod.get('nombre', '').strip()
            if not nombre:
                continue
            insumo, _ = Insumo.objects.get_or_create(
                nombre=nombre,
                defaults={'tipo': 'OTRO', 'unidad': prod.get('unidad_dosis', 'L')},
            )
            LaborInsumo.objects.get_or_create(
                labor=labor,
                insumo=insumo,
                defaults={
                    'dosis': prod.get('dosis'),
                    'total_aplicado': prod.get('total'),
                    'unidad_dosis': prod.get('unidad_dosis', 'L/ha'),
                },
            )
