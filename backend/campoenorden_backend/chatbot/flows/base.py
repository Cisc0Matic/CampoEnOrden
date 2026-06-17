import logging
import re
from datetime import date, datetime

logger = logging.getLogger(__name__)

CULTIVOS_LIST = ['Trigo', 'Soja 1', 'Soja 2', 'Maiz', 'Girasol', 'Sorgo', 'Mani', 'CS']
CULTIVOS_MENU = '1.Trigo  2.Soja 1  3.Soja 2  4.Maiz  5.Girasol  6.Sorgo  7.Mani  8.CS'


def parse_product(text: str) -> dict:
    """Parse 'PRODUCTO - DOSIS/HA - TOTAL' from the right so product names with dashes work."""
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

    def handle(self, message: str, media_id: str = None, mime_type: str = None) -> str:
        upper = (message or '').strip().upper()
        if upper in ('MENU', 'INICIO', '/START'):
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
            return 'Ocurrio un error inesperado. Escribe *MENU* para volver al inicio.'

    def _advance_to(self, step: int) -> None:
        self.session.current_step = step
        self.session.session_data = self.data
        self.session.save(update_fields=['current_step', 'session_data', 'last_activity'])

    def _save_data(self, **kwargs) -> None:
        self.data.update(kwargs)
        self.session.session_data = self.data
        self.session.save(update_fields=['session_data', 'last_activity'])

    def _go_to_menu(self) -> str:
        from chatbot.flows.menu import show_main_menu
        self.session.current_flow = ''
        self.session.current_step = 0
        self.session.session_data = {}
        self.session.save(update_fields=['current_flow', 'current_step', 'session_data', 'last_activity'])
        return show_main_menu(self.session.user)

    def _cancel(self) -> str:
        self.session.current_flow = ''
        self.session.current_step = 0
        self.session.session_data = {}
        self.session.save(update_fields=['current_flow', 'current_step', 'session_data', 'last_activity'])
        return 'Operacion cancelada. Escribi *MENU* para volver al inicio.'

    def _invalid(self, n: int) -> str:
        return f'Opcion no valida. Escribi un numero del 1 al {n}.'

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

    def _get_campos(self):
        from core.models import Campo
        return list(Campo.objects.filter(estado_contrato='ACTIVO').order_by('nombre'))

    def _get_campana_activa(self):
        from core.models import Campana
        return Campana.objects.filter(activa=True).first()

    def _get_lotes(self, campo_id: int):
        from core.models import Lote
        campana = self._get_campana_activa()
        if campana:
            return list(Lote.objects.filter(campo_id=campo_id, campana=campana, activo=True).order_by('nombre'))
        return list(Lote.objects.filter(campo_id=campo_id, activo=True).order_by('nombre'))

    def _get_maquinaria(self):
        from chatbot.models import Maquinaria
        return list(Maquinaria.objects.filter(activo=True).order_by('tipo', 'nombre'))

    def _step_ask_campo(self) -> str:
        campos = self._get_campos()
        if not campos:
            return 'No hay campos activos registrados. Escribi *MENU* para volver.'
        opts = '\n'.join(f'{i+1}. {c.nombre}' for i, c in enumerate(campos))
        self.data = {'campos_ids': [c.id for c in campos]}
        self._advance_to(1)
        return f'En que campo?\n\n{opts}'

    def _step_process_campo_ask_lote(self, message: str) -> str:
        campos_ids = self.data.get('campos_ids', [])
        n = self._parse_int(message, 1, len(campos_ids))
        if n is None:
            return self._invalid(len(campos_ids))
        from core.models import Campo
        campo = Campo.objects.get(id=campos_ids[n - 1])
        lotes = self._get_lotes(campo.id)
        if not lotes:
            return 'No hay lotes registrados en este campo para la campana activa.\n\nEscribi *MENU* para volver.'
        opts = '\n'.join(f'{i+1}. {l.nombre} ({l.superficie} ha)' for i, l in enumerate(lotes))
        self.data.update({'campo_id': campo.id, 'campo_nombre': campo.nombre, 'lotes_ids': [l.id for l in lotes]})
        self._advance_to(2)
        return f'En que lote?\n\n{opts}'

    def _step_process_lote(self, message: str, next_step: int, next_prompt: str) -> str:
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
            f'Producto {n} — usa el formato:\n'
            'PRODUCTO - DOSIS/HA - TOTAL\n'
            'Ej: Roundup - 3 L/ha - 15 L\n\n'
            'Cuando termines todos los productos escribi *LISTO*'
        )

    def _products_loop(self, message: str, next_step: int, next_prompt: str) -> str:
        if message.strip().upper() == 'LISTO':
            if not self.data.get('productos'):
                return 'Debes cargar al menos un producto antes de continuar.\n\n' + self._products_prompt(0)
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
                'Formato incorrecto. Usa: PRODUCTO - DOSIS/HA - TOTAL\n'
                'Ej: Roundup - 3 L/ha - 15 L\n\n'
                'O escribe *LISTO* para terminar.'
            )

    def _confirmation_block(self, title: str, rows: list) -> str:
        lines = [f'*{title}*', '']
        for label, value in rows:
            lines.append(f'*{label}:* {value}')
        lines.extend(['', '1. Confirmar', '2. Corregir (reinicia desde el principio)', '3. Cancelar'])
        return '\n'.join(lines)

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
