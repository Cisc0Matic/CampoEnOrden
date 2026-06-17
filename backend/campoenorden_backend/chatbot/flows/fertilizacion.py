import logging

from django.utils import timezone

from .base import BaseFlow, CULTIVOS_LIST, CULTIVOS_MENU

logger = logging.getLogger(__name__)

_TIPO_FERT = {
    '1': ('INCORPORADO', 'FERTILIZACION_TERRESTRE'),
    '2': ('VOLEO', 'FERTILIZACION_TERRESTRE'),
    '3': ('AEREO', None),
    '4': ('FERTIRRIGACION', 'FERTILIZACION_TERRESTRE'),
}
_EQUIPO_AEREO = {'1': ('AVION', 'FERTILIZACION_TERRESTRE'), '2': ('DRONE', 'FERTILIZACION_DRONES')}


class FertilizacionFlow(BaseFlow):
    FLOW_NAME = 'fertilizacion'

    def step_0(self, message, media_id, mime_type):
        return self._step_ask_campo()

    def step_1(self, message, media_id, mime_type):
        return self._step_process_campo_ask_lote(message)

    def step_2(self, message, media_id, mime_type):
        return self._step_process_lote(message, 3, 'Fecha? (DD/MM/AA o HOY)')

    def step_3(self, message, media_id, mime_type):
        fecha = self._parse_date(message)
        if not fecha:
            return 'Formato incorrecto. Usa DD/MM/AA o escribe HOY.'
        self.data.update({'fecha': fecha.isoformat(), 'productos': []})
        self._advance_to(4)
        return f'Cultivo?\n\n{CULTIVOS_MENU}'

    def step_4(self, message, media_id, mime_type):
        n = self._parse_int(message, 1, len(CULTIVOS_LIST))
        if n is None:
            return self._invalid(len(CULTIVOS_LIST))
        self.data['cultivo'] = CULTIVOS_LIST[n - 1]
        self._advance_to(5)
        return 'Tipo de fertilizacion?\n\n1. Incorporado\n2. Voleo\n3. Aereo\n4. Fertirrigacion'

    def step_5(self, message, media_id, mime_type):
        entry = _TIPO_FERT.get(message.strip())
        if not entry:
            return self._invalid(4)
        subtipo, tipo_labor = entry
        self.data['subtipo_fert'] = subtipo
        if subtipo == 'AEREO':
            self.data['tipo'] = None
            self._advance_to(6)
            return 'Equipo aereo?\n\n1. Avion\n2. Drone'
        self.data['tipo'] = tipo_labor
        self._advance_to(7)
        return self._products_prompt(0)

    def step_6(self, message, media_id, mime_type):
        entry = _EQUIPO_AEREO.get(message.strip())
        if not entry:
            return self._invalid(2)
        equipo, tipo_labor = entry
        self.data.update({'equipo_aereo': equipo, 'tipo': tipo_labor})
        self._advance_to(7)
        return self._products_prompt(0)

    def step_7(self, message, media_id, mime_type):
        is_aereo = self.data.get('subtipo_fert') == 'AEREO'
        if is_aereo:
            opts = '1. Personal propio\n2. Contratista drone\n3. Contratista avion'
            max_opt = 3
        else:
            opts = '1. Personal propio\n2. Contratista'
            max_opt = 2
        return self._products_loop(message, 8, f'Quien realizo?\n\n{opts}')

    def step_8(self, message, media_id, mime_type):
        is_aereo = self.data.get('subtipo_fert') == 'AEREO'
        max_opt = 3 if is_aereo else 2
        opt = self._parse_int(message, 1, max_opt)
        if opt is None:
            return self._invalid(max_opt)
        ejecutor_map = {1: 'PERSONAL_PROPIO', 2: 'CONTRATISTA_DRONE', 3: 'CONTRATISTA_AVION'}
        self.data['ejecutor'] = ejecutor_map.get(opt, 'PERSONAL_PROPIO')
        self._advance_to(9)
        return 'Observacion?\n\n1. Si\n2. No'

    def step_9(self, message, media_id, mime_type):
        opt = self._parse_int(message, 1, 2)
        if opt is None:
            return self._invalid(2)
        if opt == 1:
            self._advance_to(10)
            return 'Escribi tu observacion:'
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

    def _build_confirmation(self) -> str:
        d = self.data
        prods = d.get('productos', [])
        prods_lines = '\n'.join(
            f"  - {p['nombre']}: {p['dosis_str']} | Total: {p['total_str']}" for p in prods
        ) or '  (sin productos)'
        subtipo = d.get('subtipo_fert', '-')
        equipo = d.get('equipo_aereo', '')
        tipo_display = subtipo + (f' ({equipo})' if equipo else '')
        ejecutor_display = d.get('ejecutor', '-').replace('_', ' ').capitalize()
        rows = [
            ('Campo', d.get('campo_nombre', '-')),
            ('Lote', f"{d.get('lote_nombre', '-')} ({d.get('hectareas', '-')} ha)"),
            ('Fecha', d.get('fecha', '-')),
            ('Cultivo', d.get('cultivo', '-')),
            ('Tipo', tipo_display),
            ('Quien realizo', ejecutor_display),
        ]
        if d.get('observacion'):
            rows.append(('Observacion', d['observacion']))
        block = self._confirmation_block('Confirmar Fertilizacion', rows)
        return block.replace(
            '*Confirmar Fertilizacion*\n',
            f'*Confirmar Fertilizacion*\n\n*Productos:*\n{prods_lines}\n',
        )

    def _confirm_save(self) -> str:
        d = self.data
        from core.models import Labor, Lote
        try:
            lote = Lote.objects.get(id=d['lote_id'])
            tipo = d.get('tipo') or 'FERTILIZACION_TERRESTRE'
            obs_parts = [f"Tipo: {d.get('subtipo_fert', '')}"]
            if d.get('equipo_aereo'):
                obs_parts.append(f"Equipo: {d['equipo_aereo']}")
            if d.get('ejecutor', 'PERSONAL_PROPIO') != 'PERSONAL_PROPIO':
                obs_parts.append(f"Ejecutor: {d['ejecutor']}")
            if d.get('observacion'):
                obs_parts.append(d['observacion'])
            labor = Labor.objects.create(
                lote=lote,
                tipo=tipo,
                estado='CARGADA',
                fecha=d['fecha'],
                hectareas=d.get('hectareas', 0),
                observaciones='\n'.join(obs_parts),
                cargada_por=self.session.user,
                fecha_hora_carga=timezone.now(),
            )
            self._save_insumo_usage(labor, d.get('productos', []))
        except Exception as e:
            logger.exception(f'Error saving fertilizacion: {e}')
            return 'Error al guardar. Por favor intenta de nuevo.'

        return (
            f"Fertilizacion registrada en {d.get('lote_nombre', 'el lote')}.\n\n"
            'Escribi *MENU* para volver al inicio.'
        )
