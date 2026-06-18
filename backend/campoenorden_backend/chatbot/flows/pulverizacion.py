import logging

from django.utils import timezone

from .base import BaseFlow, CULTIVOS_LIST

logger = logging.getLogger(__name__)

_TIPO_MAP = {'1': 'PULVERIZACION_TERRESTRE', '2': 'PULVERIZACION_AEREA'}
_TIPO_DISPLAY = {'PULVERIZACION_TERRESTRE': 'Terrestre', 'PULVERIZACION_AEREA': 'Aerea'}


class PulverizacionFlow(BaseFlow):
    FLOW_NAME = 'pulverizacion'

    def step_0(self, message, media_id, mime_type):
        return self._step_ask_campo()

    def step_1(self, message, media_id, mime_type):
        return self._step_process_campo_ask_lote(message)

    def step_2(self, message, media_id, mime_type):
        result = self._step_process_lote(message, 3, '')
        if isinstance(result, dict):
            return result
        return self._reply_buttons('Tipo de pulverización?', [
            {'type': 'reply', 'reply': {'id': '1', 'title': 'Terrestre'}},
            {'type': 'reply', 'reply': {'id': '2', 'title': 'Aérea'}},
            {'type': 'reply', 'reply': {'id': 'GO_MENU', 'title': '📋 Menú'}},
        ])

    def step_3(self, message, media_id, mime_type):
        tipo = _TIPO_MAP.get(message.strip())
        if not tipo:
            return self._invalid(2)
        self.data['tipo'] = tipo
        self._advance_to(4)
        return 'Fecha? (DD/MM/AA o HOY)'

    def step_4(self, message, media_id, mime_type):
        fecha = self._parse_date(message)
        if not fecha:
            return 'Formato incorrecto. Usá DD/MM/AA o escribí HOY.'
        self.data.update({'fecha': fecha.isoformat(), 'productos': []})
        self._advance_to(5)
        return self._cultivo_list()

    def step_5(self, message, media_id, mime_type):
        n = self._parse_int(message, 1, len(CULTIVOS_LIST))
        if n is None:
            return self._invalid(len(CULTIVOS_LIST))
        self.data.update({'cultivo': CULTIVOS_LIST[n - 1], 'productos': []})
        self._advance_to(6)
        return self._products_prompt(0)

    def step_6(self, message, media_id, mime_type):
        return self._products_loop(message, 7, '¿Quién realizó?')

    def step_7(self, message, media_id, mime_type):
        opt = self._parse_int(message, 1, 2)
        if opt is None:
            return self._who_buttons('¿Quién realizó la pulverización?')
        self.data['ejecutor'] = 'PERSONAL_PROPIO' if opt == 1 else 'CONTRATISTA'
        self._advance_to(9)
        return self._yes_no_buttons('¿Observación?')

    def step_9(self, message, media_id, mime_type):
        opt = self._parse_int(message, 1, 2)
        if opt is None:
            return self._invalid(2)
        if opt == 1:
            self._advance_to(10)
            return 'Escribí tu observación:'
        self.data['observacion'] = ''
        self._advance_to(11)
        return self._build_confirmation()

    def step_10(self, message, media_id, mime_type):
        self.data['observacion'] = message.strip()
        self._advance_to(11)
        return self._build_confirmation()

    def step_11(self, message, media_id, mime_type):
        opt = self._parse_int(message, 1, 3)
        if opt == 1:
            return self._confirm_save()
        if opt == 2:
            self._restart_flow()
            return self.step_0('', None, None)
        if opt == 3:
            return self._cancel()
        return self._invalid(3)

    def _build_confirmation(self) -> dict:
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
            ('Quien realizó', ejecutor_display),
        ]
        if d.get('observacion'):
            rows.append(('Observación', d['observacion']))
        block = self._confirmation_block('Confirmar Pulverización', rows)
        block['body'] = block['body'].replace(
            '*Confirmar Pulverización*\n',
            f'*Confirmar Pulverización*\n\n*Productos:*\n{prods_lines}\n',
        )
        return block

    def _confirm_save(self) -> dict:
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
            return self._with_menu('Error al guardar. Por favor intentá de nuevo o contactá al administrador.')

        from chatbot.flows.menu import get_labores_submenu
        return self._finish_with_submenu(
            f"✅ Pulverización registrada en {d.get('lote_nombre', 'el lote')}.",
            get_labores_submenu,
        )
