import logging

from django.utils import timezone

from .base import BaseFlow, CULTIVOS_LIST, CULTIVOS_MENU

logger = logging.getLogger(__name__)


class CosechaFlow(BaseFlow):
    FLOW_NAME = 'cosecha'

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
        self.data['fecha'] = fecha.isoformat()
        self._advance_to(4)
        return f'Cultivo cosechado?\n\n{CULTIVOS_MENU}'

    def step_4(self, message, media_id, mime_type):
        n = self._parse_int(message, 1, len(CULTIVOS_LIST))
        if n is None:
            return self._invalid(len(CULTIVOS_LIST))
        self.data['cultivo'] = CULTIVOS_LIST[n - 1]
        self._advance_to(5)
        return (
            'Como queris cargar la cosecha?\n\n'
            '1. Foto del monitor\n'
            '2. Foto monitor + mapa de rendimiento\n'
            '3. Carga manual'
        )

    # step_5: process modo selection
    def step_5(self, message, media_id, mime_type):
        modo_map = {'1': 'FOTO', '2': 'FOTO_MAPA', '3': 'MANUAL'}
        modo = modo_map.get(message.strip())
        if not modo:
            return self._invalid(3)
        self.data['modo'] = modo
        self._advance_to(6)
        if modo in ('FOTO', 'FOTO_MAPA'):
            return 'Envia la foto del monitor de la cosechadora.'
        return 'Kg secos cosechados (total del lote):\nEj: 276500'

    # step_6: receive image OR kg_seco
    def step_6(self, message, media_id, mime_type):
        modo = self.data.get('modo', 'MANUAL')

        if modo in ('FOTO', 'FOTO_MAPA'):
            if not media_id:
                return 'Por favor envia la foto del monitor de la cosechadora.'
            extracted = self._run_vision(media_id, mime_type)
            self.data['vision_data'] = extracted
            self._advance_to(7)
            if extracted:
                resumen = (
                    'Datos extraidos del monitor:\n\n'
                    f"Kg secos: {extracted.get('kg_seco', '?')}\n"
                    f"Kg humedos: {extracted.get('kg_humedo', '?')}\n"
                    f"Humedad: {extracted.get('humedad_pct', '?')}%\n"
                    f"Hectareas: {extracted.get('hectareas', self.data.get('hectareas', '?'))}\n"
                    f"Total kg: {extracted.get('total_kg', '?')}\n\n"
                    '1. Confirmar estos datos\n'
                    '2. Corregir / carga manual'
                )
            else:
                resumen = (
                    'No pude leer el monitor automaticamente.\n\n'
                    '1. Intentar con otra foto\n'
                    '2. Carga manual'
                )
            return resumen

        # MANUAL mode: process kg_seco
        val = self._parse_float(message)
        if val is None:
            return 'Ingresa un numero valido (Ej: 276500).'
        self.data['kg_seco'] = val
        self._advance_to(7)
        return f'Hectareas cosechadas:\nEj: {self.data.get("hectareas", "52.5")}'

    # step_7: confirm vision OR process ha
    def step_7(self, message, media_id, mime_type):
        modo = self.data.get('modo', 'MANUAL')

        if modo in ('FOTO', 'FOTO_MAPA'):
            opt = self._parse_int(message, 1, 2)
            if opt is None:
                return self._invalid(2)
            if opt == 1:
                v = self.data.get('vision_data', {})
                self.data.update({
                    'kg_seco': v.get('kg_seco') or v.get('total_kg'),
                    'kg_humedo': v.get('kg_humedo'),
                    'humedad_pct': v.get('humedad_pct'),
                    'ha_cosecha': v.get('hectareas') or self.data.get('hectareas'),
                    'total_kg': v.get('total_kg') or v.get('kg_seco'),
                })
                self._advance_to(10)
                return 'Quien realizo la cosecha?\n\n1. Personal propio\n2. Contratista'
            # Switch to manual
            self.data['modo'] = 'MANUAL'
            self._advance_to(6)
            return 'Kg secos cosechados (total del lote):\nEj: 276500'

        # MANUAL: process ha
        val = self._parse_float(message)
        if val is None:
            return 'Ingresa un numero valido (Ej: 52.5).'
        self.data['ha_cosecha'] = val
        self._advance_to(8)
        return 'Humedad % al momento de cosecha:\nEj: 13.5'

    # step_8: MANUAL — process humedad
    def step_8(self, message, media_id, mime_type):
        val = self._parse_float(message)
        if val is None:
            return 'Ingresa un numero valido (Ej: 13.5).'
        self.data['humedad_pct'] = val
        self._advance_to(9)
        return 'Total kg secos cosechados (con descuento de humedad):\nEj: 276236'

    # step_9: MANUAL — process total kg
    def step_9(self, message, media_id, mime_type):
        val = self._parse_float(message)
        if val is None:
            return 'Ingresa un numero valido.'
        self.data['total_kg'] = val
        self._advance_to(10)
        return 'Quien realizo la cosecha?\n\n1. Personal propio\n2. Contratista'

    # step_10: quien realizó
    def step_10(self, message, media_id, mime_type):
        opt = self._parse_int(message, 1, 2)
        if opt is None:
            return self._invalid(2)
        self.data['ejecutor'] = 'PERSONAL_PROPIO' if opt == 1 else 'CONTRATISTA'
        self._advance_to(11)
        return 'Observacion?\n\n1. Si\n2. No'

    # step_11: observacion y/n
    def step_11(self, message, media_id, mime_type):
        opt = self._parse_int(message, 1, 2)
        if opt is None:
            return self._invalid(2)
        if opt == 1:
            self._advance_to(12)
            return 'Escribi tu observacion:'
        self.data['observacion'] = ''
        self._advance_to(13)
        return self._build_confirmation()

    # step_12: observacion text
    def step_12(self, message, media_id, mime_type):
        self.data['observacion'] = message.strip()
        self._advance_to(13)
        return self._build_confirmation()

    # step_13: final confirmation
    def step_13(self, message, media_id, mime_type):
        opt = self._parse_int(message, 1, 3)
        if opt == 1:
            return self._confirm_save()
        if opt == 2:
            self._restart_flow()
            return self.step_0('', None, None)
        if opt == 3:
            return self._cancel()
        return self._invalid(3)

    def _run_vision(self, media_id: str, mime_type: str) -> dict:
        try:
            from chatbot.services.whatsapp import WhatsAppService
            from chatbot.services.claude_vision import ClaudeVisionService
            wa = WhatsAppService()
            media_url = wa.get_media_url(media_id)
            if not media_url:
                return {}
            image_bytes = wa.download_media(media_url)
            if not image_bytes:
                return {}
            vision = ClaudeVisionService()
            return vision.analyze_cosecha_monitor(image_bytes, mime_type or 'image/jpeg')
        except Exception as e:
            logger.exception(f'Cosecha vision error: {e}')
            return {}

    def _calc_qq_ha(self) -> float:
        total_kg = float(self.data.get('total_kg') or self.data.get('kg_seco') or 0)
        ha = float(self.data.get('ha_cosecha') or self.data.get('hectareas') or 1)
        return round(total_kg / ha / 100, 2) if ha > 0 else 0

    def _build_confirmation(self) -> str:
        d = self.data
        total_kg = d.get('total_kg') or d.get('kg_seco') or 0
        qq_ha = self._calc_qq_ha()
        ejecutor_display = 'Personal propio' if d.get('ejecutor') == 'PERSONAL_PROPIO' else 'Contratista'
        rows = [
            ('Campo', d.get('campo_nombre', '-')),
            ('Lote', f"{d.get('lote_nombre', '-')} ({d.get('hectareas', '-')} ha)"),
            ('Fecha', d.get('fecha', '-')),
            ('Cultivo', d.get('cultivo', '-')),
            ('Total kg secos', str(total_kg)),
            ('Humedad', f"{d.get('humedad_pct', '-')}%"),
            ('Rinde', f'{qq_ha} qq/ha'),
            ('Quien realizo', ejecutor_display),
        ]
        if d.get('observacion'):
            rows.append(('Observacion', d['observacion']))
        return self._confirmation_block('Confirmar Cosecha', rows)

    def _confirm_save(self) -> str:
        d = self.data
        from core.models import Labor, Lote
        try:
            lote = Lote.objects.get(id=d['lote_id'])
            total_kg = float(d.get('total_kg') or d.get('kg_seco') or 0)
            ha = float(d.get('ha_cosecha') or d.get('hectareas') or 1)
            qq_ha = round(total_kg / ha / 100, 2) if ha > 0 else 0
            obs_parts = []
            modo = d.get('modo', 'MANUAL')
            if modo != 'MANUAL':
                obs_parts.append(f"Carga: {modo.replace('_', ' ').title()} (Claude Vision)")
            if d.get('kg_humedo'):
                obs_parts.append(f"Kg humedos: {d['kg_humedo']}")
            if d.get('humedad_pct'):
                obs_parts.append(f"Humedad: {d['humedad_pct']}%")
            if d.get('kg_seco'):
                obs_parts.append(f"Kg secos: {d['kg_seco']}")
            obs_parts.append(f'Total kg: {total_kg}')
            if d.get('ejecutor') == 'CONTRATISTA':
                obs_parts.append('Ejecutor: Contratista')
            if d.get('observacion'):
                obs_parts.append(d['observacion'])
            Labor.objects.create(
                lote=lote,
                tipo='COSECHA',
                estado='CARGADA',
                fecha=d['fecha'],
                hectareas=ha,
                qq_ha=qq_ha,
                observaciones='\n'.join(obs_parts),
                cargada_por=self.session.user,
                fecha_hora_carga=timezone.now(),
            )
        except Exception as e:
            logger.exception(f'Error saving cosecha: {e}')
            return 'Error al guardar. Por favor intenta de nuevo.'

        qq_ha_val = self._calc_qq_ha()
        return (
            f"Cosecha registrada en {d.get('lote_nombre', 'el lote')}.\n"
            f"Total: {d.get('total_kg', d.get('kg_seco', 0))} kg | Rinde: {qq_ha_val} qq/ha\n\n"
            'Escribi *MENU* para volver al inicio.'
        )
