import logging

from django.utils import timezone

from .base import BaseFlow, CULTIVOS_LIST, CULTIVOS_MENU

logger = logging.getLogger(__name__)

_TIPO_MAP = {'1': 'PULVERIZACION_TERRESTRE', '2': 'PULVERIZACION_AEREA'}
_TIPO_DISPLAY = {'PULVERIZACION_TERRESTRE': 'Terrestre', 'PULVERIZACION_AEREA': 'Aerea'}


class PulverizacionFlow(BaseFlow):
    FLOW_NAME = 'pulverizacion'

    # step_0: ask campo (message is ignored — called on flow start)
    def step_0(self, message, media_id, mime_type):
        return self._step_ask_campo()

    # step_1: process campo → ask lote
    def step_1(self, message, media_id, mime_type):
        return self._step_process_campo_ask_lote(message)

    # step_2: process lote → ask tipo
    def step_2(self, message, media_id, mime_type):
        return self._step_process_lote(message, 3, 'Tipo?\n\n1. Terrestre\n2. Aerea')

    # step_3: process tipo → ask fecha
    def step_3(self, message, media_id, mime_type):
        tipo = _TIPO_MAP.get(message.strip())
        if not tipo:
            return self._invalid(2)
        self.data['tipo'] = tipo
        self._advance_to(4)
        return 'Fecha? (DD/MM/AA o HOY)'

    # step_4: process fecha → ask cultivo
    def step_4(self, message, media_id, mime_type):
        fecha = self._parse_date(message)
        if not fecha:
            return 'Formato incorrecto. Usa DD/MM/AA o escribe HOY.'
        self.data.update({'fecha': fecha.isoformat(), 'productos': []})
        self._advance_to(5)
        return f'Cultivo?\n\n{CULTIVOS_MENU}'

    # step_5: process cultivo → start product loop
    def step_5(self, message, media_id, mime_type):
        n = self._parse_int(message, 1, len(CULTIVOS_LIST))
        if n is None:
            return self._invalid(len(CULTIVOS_LIST))
        self.data.update({'cultivo': CULTIVOS_LIST[n - 1], 'productos': []})
        self._advance_to(6)
        return self._products_prompt(0)

    # step_6: product loop (stays on step 6 until LISTO)
    def step_6(self, message, media_id, mime_type):
        return self._products_loop(message, 7, 'Quien realizo?\n\n1. Personal propio\n2. Contratista')

    # step_7: quien realizó → ask observacion
    def step_7(self, message, media_id, mime_type):
        opt = self._parse_int(message, 1, 2)
        if opt is None:
            return self._invalid(2)
        self.data['ejecutor'] = 'PERSONAL_PROPIO' if opt == 1 else 'CONTRATISTA'
        self._advance_to(8)
        return 'Observacion?\n\n1. Si\n2. No'

    # step_8: observacion yes/no
    def step_8(self, message, media_id, mime_type):
        opt = self._parse_int(message, 1, 2)
        if opt is None:
            return self._invalid(2)
        if opt == 1:
            self._advance_to(9)
            return 'Escribi tu observacion:'
        self.data['observacion'] = ''
        self._advance_to(10)
        return self._build_confirmation()

    # step_9: observacion text
    def step_9(self, message, media_id, mime_type):
        self.data['observacion'] = message.strip()
        self._advance_to(10)
        return self._build_confirmation()

    # step_10: final confirmation
    def step_10(self, message, media_id, mime_type):
        opt = self._parse_int(message, 1, 3)
        if opt == 1:
            return self._confirm_save()
        if opt == 2:
            self._restart_flow()
            return self.step_0('', None, None)
        if opt == 3:
            return self._cancel()
        return self._invalid(3)

    def _build_confirmation(self) -> str:
        d = self.data
        prods = d.get('productos', [])
        prods_lines = '\n'.join(
            f"  - {p['nombre']}: {p['dosis_str']} | Total: {p['total_str']}" for p in prods
        ) or '  (sin productos)'
        tipo_display = _TIPO_DISPLAY.get(d.get('tipo', ''), '-')
        ejecutor_display = 'Personal propio' if d.get('ejecutor') == 'PERSONAL_PROPIO' else 'Contratista'
        rows = [
            ('Campo', d.get('campo_nombre', '-')),
            ('Lote', f"{d.get('lote_nombre', '-')} ({d.get('hectareas', '-')} ha)"),
            ('Tipo', tipo_display),
            ('Fecha', d.get('fecha', '-')),
            ('Cultivo', d.get('cultivo', '-')),
            ('Quien realizo', ejecutor_display),
        ]
        if d.get('observacion'):
            rows.append(('Observacion', d['observacion']))
        block = self._confirmation_block('Confirmar Pulverizacion', rows)
        return block.replace(
            '*Confirmar Pulverizacion*\n',
            f'*Confirmar Pulverizacion*\n\n*Productos:*\n{prods_lines}\n',
        )

    def _confirm_save(self) -> str:
        d = self.data
        from core.models import Labor, Lote
        try:
            lote = Lote.objects.get(id=d['lote_id'])
            obs_parts = []
            if d.get('ejecutor') == 'CONTRATISTA':
                obs_parts.append('Ejecutor: Contratista')
            if d.get('observacion'):
                obs_parts.append(d['observacion'])
            labor = Labor.objects.create(
                lote=lote,
                tipo=d['tipo'],
                estado='CARGADA',
                fecha=d['fecha'],
                hectareas=d.get('hectareas', 0),
                observaciones='\n'.join(obs_parts),
                cargada_por=self.session.user,
                fecha_hora_carga=timezone.now(),
            )
            self._save_insumo_usage(labor, d.get('productos', []))
        except Exception as e:
            logger.exception(f'Error saving pulverizacion: {e}')
            return 'Error al guardar. Por favor intenta de nuevo o contacta al administrador.'

        return (
            f"Pulverizacion registrada correctamente en {d.get('lote_nombre', 'el lote')}.\n\n"
            'Escribi *MENU* para volver al inicio.'
        )
