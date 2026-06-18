import logging

from django.utils import timezone

from .base import BaseFlow, CULTIVOS_LIST

logger = logging.getLogger(__name__)


class SiembraFlow(BaseFlow):
    FLOW_NAME = 'siembra'

    def step_0(self, message, media_id, mime_type):
        return self._step_ask_campo()

    def step_1(self, message, media_id, mime_type):
        return self._step_process_campo_ask_lote(message)

    def step_2(self, message, media_id, mime_type):
        result = self._step_process_lote(message, 3, 'Fecha? (DD/MM/AA o HOY)')
        if isinstance(result, dict):
            return result
        return result

    def step_3(self, message, media_id, mime_type):
        fecha = self._parse_date(message)
        if not fecha:
            return 'Formato incorrecto. Usa DD/MM/AA o escribe HOY.'
        self.data['fecha'] = fecha.isoformat()
        self._advance_to(4)
        return self._cultivo_list('Cultivo a sembrar?')

    def step_4(self, message, media_id, mime_type):
        n = self._parse_int(message, 1, len(CULTIVOS_LIST))
        if n is None:
            return self._invalid(len(CULTIVOS_LIST))
        self.data['cultivo'] = CULTIVOS_LIST[n - 1]
        self._advance_to(5)
        return 'Variedad? (texto libre, Ej: DM 46i20)'

    def step_5(self, message, media_id, mime_type):
        if not message.strip():
            return 'Por favor escribi la variedad.'
        self.data['variedad'] = message.strip()
        self._advance_to(6)
        return 'Densidad (granos por metro)?\nEj: 23,2'

    def step_6(self, message, media_id, mime_type):
        val = self._parse_float(message)
        if val is None:
            return 'Ingresa un numero valido (Ej: 23,2).'
        self.data['densidad'] = val
        self._advance_to(7)
        return 'Distancia entre surcos (cm)?\nEj: 52'

    def step_7(self, message, media_id, mime_type):
        val = self._parse_float(message)
        if val is None:
            return 'Ingresa un numero valido (Ej: 52).'
        self.data['distancia_surcos'] = val
        self._advance_to(8)
        return (
            'PMS — Peso de mil semillas (gramos)?\n'
            'Ej: 180\n\n'
            '(API semilleros en desarrollo — carga manual por ahora)'
        )

    def step_8(self, message, media_id, mime_type):
        val = self._parse_float(message)
        if val is None:
            return 'Ingresa un numero valido (Ej: 180).'
        self.data['pms'] = val
        # Calculate kg/ha automatically
        densidad = self.data.get('densidad', 0)
        surcos = self.data.get('distancia_surcos', 52)
        if densidad and surcos:
            kg_ha = round((densidad * val * 10) / surcos, 1)
            self.data['kg_semilla_ha'] = kg_ha
        self._advance_to(9)
        kg_info = f"Kg semilla/ha calculado: {self.data.get('kg_semilla_ha', '-')}\n\n" if self.data.get('kg_semilla_ha') else ''
        return self._yes_no_buttons(f'{kg_info}¿Curasemillas e inoculante?')

    # step_9: curasemillas?
    def step_9(self, message, media_id, mime_type):
        opt = self._parse_int(message, 1, 2)
        if opt is None:
            return self._invalid(2)
        self.data['tiene_curasemillas'] = (opt == 1)
        self.data['productos_cs'] = []
        if opt == 1:
            self._advance_to(10)
            return self._products_prompt(0) + '\n(Curasemillas e inoculante)'
        # Skip to fertilizacion en siembra
        self._advance_to(12)
        return self._yes_no_buttons('¿Fertilización en siembra?')

    # step_10: curasemillas product loop
    def step_10(self, message, media_id, mime_type):
        from .base import parse_product
        if message.strip().upper() == 'LISTO':
            self.data['productos_cs'] = self.data.get('productos_cs', [])
            self._advance_to(12)
            return self._yes_no_buttons('¿Fertilización en siembra?')
        try:
            prod = parse_product(message)
            prods = self.data.get('productos_cs', [])
            prods.append(prod)
            self.data['productos_cs'] = prods
            self._save_data()
            return f'CS/Inoculante {len(prods)} cargado: {prod["nombre"]}.\n\n' + self._products_prompt(len(prods)) + '\nO escribe *LISTO* para continuar.'
        except ValueError:
            return 'Formato incorrecto. Usa: PRODUCTO - DOSIS/HA - TOTAL\nO escribe *LISTO* para continuar.'

    # step_12: fertilizacion en siembra?
    def step_12(self, message, media_id, mime_type):
        opt = self._parse_int(message, 1, 2)
        if opt is None:
            return self._invalid(2)
        self.data['tiene_fertilizante_siembra'] = (opt == 1)
        self.data['productos_fert'] = []
        if opt == 1:
            self._advance_to(13)
            return self._products_prompt(0) + '\n(Fertilizante en siembra)'
        self._advance_to(15)
        return self._who_buttons('¿Quién realizó la siembra?')

    # step_13: fertilizante en siembra product loop
    def step_13(self, message, media_id, mime_type):
        from .base import parse_product
        if message.strip().upper() == 'LISTO':
            self._advance_to(15)
            return self._who_buttons('¿Quién realizó la siembra?')
        try:
            prod = parse_product(message)
            prods = self.data.get('productos_fert', [])
            prods.append(prod)
            self.data['productos_fert'] = prods
            self._save_data()
            return f'Fertilizante {len(prods)} cargado: {prod["nombre"]}.\n\n' + self._products_prompt(len(prods)) + '\nO escribe *LISTO* para continuar.'
        except ValueError:
            return 'Formato incorrecto. Usa: PRODUCTO - DOSIS/HA - TOTAL\nO escribe *LISTO* para continuar.'

    # step_15: quien realizó
    def step_15(self, message, media_id, mime_type):
        opt = self._parse_int(message, 1, 2)
        if opt is None:
            return self._invalid(2)
        self.data['ejecutor'] = 'PERSONAL_PROPIO' if opt == 1 else 'CONTRATISTA'
        self._advance_to(16)
        return self._yes_no_buttons('¿Observación?')

    # step_16: observacion y/n
    def step_16(self, message, media_id, mime_type):
        opt = self._parse_int(message, 1, 2)
        if opt is None:
            return self._invalid(2)
        if opt == 1:
            self._advance_to(17)
            return 'Escribi tu observacion:'
        self.data['observacion'] = ''
        self._advance_to(18)
        return self._build_confirmation()

    # step_17: observacion text
    def step_17(self, message, media_id, mime_type):
        self.data['observacion'] = message.strip()
        self._advance_to(18)
        return self._build_confirmation()

    # step_18: final confirmation
    def step_18(self, message, media_id, mime_type):
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
        cs_prods = d.get('productos_cs', [])
        fert_prods = d.get('productos_fert', [])
        ejecutor_display = 'Personal propio' if d.get('ejecutor') == 'PERSONAL_PROPIO' else 'Contratista'
        rows = [
            ('Campo', d.get('campo_nombre', '-')),
            ('Lote', f"{d.get('lote_nombre', '-')} ({d.get('hectareas', '-')} ha)"),
            ('Fecha', d.get('fecha', '-')),
            ('Cultivo', d.get('cultivo', '-')),
            ('Variedad', d.get('variedad', '-')),
            ('Densidad', f"{d.get('densidad', '-')} gr/m"),
            ('Distancia surcos', f"{d.get('distancia_surcos', '-')} cm"),
            ('PMS', f"{d.get('pms', '-')} g"),
            ('Kg semilla/ha', str(d.get('kg_semilla_ha', '-'))),
            ('Quien realizo', ejecutor_display),
        ]
        if cs_prods:
            rows.append(('Curasemillas/Inoc.', ', '.join(p['nombre'] for p in cs_prods)))
        if fert_prods:
            rows.append(('Fertilizante siembra', ', '.join(p['nombre'] for p in fert_prods)))
        if d.get('observacion'):
            rows.append(('Observacion', d['observacion']))
        return self._confirmation_block('Confirmar Siembra', rows)

    def _confirm_save(self) -> dict:
        d = self.data
        from core.models import Labor, Lote
        try:
            lote = Lote.objects.get(id=d['lote_id'])
            obs_parts = [
                f"Variedad: {d.get('variedad', '-')}",
                f"Densidad: {d.get('densidad', '-')} gr/m",
                f"Distancia: {d.get('distancia_surcos', '-')} cm",
                f"PMS: {d.get('pms', '-')} g",
                f"Kg semilla/ha: {d.get('kg_semilla_ha', '-')}",
            ]
            if d.get('ejecutor') == 'CONTRATISTA':
                obs_parts.append('Ejecutor: Contratista')
            if d.get('observacion'):
                obs_parts.append(d['observacion'])
            labor = Labor.objects.create(
                lote=lote,
                tipo='SIEMBRA',
                estado='CARGADA',
                fecha=d['fecha'],
                hectareas=d.get('hectareas', 0),
                observaciones='\n'.join(obs_parts),
                cargada_por=self.session.user,
                fecha_hora_carga=timezone.now(),
            )
            all_prods = d.get('productos_cs', []) + d.get('productos_fert', [])
            self._save_insumo_usage(labor, all_prods)
        except Exception as e:
            logger.exception(f'Error saving siembra: {e}')
            return self._with_menu('Error al guardar. Por favor intenta de nuevo.')

        from chatbot.flows.menu import get_labores_submenu
        return self._finish_with_submenu(
            f"✅ Siembra registrada en {d.get('lote_nombre', 'el lote')}.",
            get_labores_submenu,
        )
