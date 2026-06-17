import logging

from .base import BaseFlow

logger = logging.getLogger(__name__)

_TIPO_MAP = {
    '1': 'SERVICE',
    '2': 'REP_MECANICA',
    '3': 'ELECTRICA',
    '4': 'NEUMATICOS',
    '5': 'CHAPA_PINTURA',
    '6': 'OTRO',
}
_TIPO_DISPLAY = {
    'SERVICE': 'Service',
    'REP_MECANICA': 'Reparacion mecanica',
    'ELECTRICA': 'Electrica',
    'NEUMATICOS': 'Neumaticos',
    'CHAPA_PINTURA': 'Chapa y pintura',
    'OTRO': 'Otro',
}
_QUIEN_MAP = {
    '1': 'PERSONAL_PROPIO',
    '2': 'TALLER',
    '3': 'CONCESIONARIO',
}
_PAGO_MAP = {
    '1': ('CHEQUE', 'Cheque'),
    '2': ('TRANSFERENCIA', 'Transferencia'),
    '3': ('TARJETA', 'Tarjeta'),
    '4': ('EFECTIVO', 'Efectivo'),
}


class MantenimientoFlow(BaseFlow):
    FLOW_NAME = 'mantenimiento'

    # step_0: ask maquina
    def step_0(self, message, media_id, mime_type):
        self.data = {}
        maquinaria = self._get_maquinaria()
        if not maquinaria:
            self.data['maquinaria_id'] = None
            self.data['maquinaria_nombre'] = 'Sin inventario'
            self._advance_to(2)
            return (
                'No hay maquinaria registrada en el inventario.\n\n'
                'Tipo de mantenimiento?\n\n'
                '1. Service\n2. Rep. mecanica\n3. Electrica\n'
                '4. Neumaticos\n5. Chapa y pintura\n6. Otro'
            )
        opts = '\n'.join(f'{i+1}. {m.nombre} ({m.tipo})' for i, m in enumerate(maquinaria))
        self.data['maquinas_ids'] = [m.id for m in maquinaria]
        self._advance_to(1)
        return f'A que maquina?\n\n{opts}'

    # step_1: process maquina → ask tipo
    def step_1(self, message, media_id, mime_type):
        maquinas_ids = self.data.get('maquinas_ids', [])
        n = self._parse_int(message, 1, len(maquinas_ids))
        if n is None:
            return self._invalid(len(maquinas_ids))
        from chatbot.models import Maquinaria
        m = Maquinaria.objects.get(id=maquinas_ids[n - 1])
        self.data.update({'maquinaria_id': m.id, 'maquinaria_nombre': m.nombre})
        self._advance_to(2)
        return (
            'Tipo de mantenimiento?\n\n'
            '1. Service\n2. Rep. mecanica\n3. Electrica\n'
            '4. Neumaticos\n5. Chapa y pintura\n6. Otro'
        )

    # step_2: process tipo → ask carga mode
    def step_2(self, message, media_id, mime_type):
        tipo = _TIPO_MAP.get(message.strip())
        if not tipo:
            return self._invalid(6)
        self.data['tipo'] = tipo
        self._advance_to(3)
        return (
            'Como queris cargar?\n\n'
            '1. Foto o PDF de la factura\n'
            '2. Carga manual'
        )

    # step_3: carga mode
    def step_3(self, message, media_id, mime_type):
        opt = self._parse_int(message, 1, 2)
        if opt is None:
            return self._invalid(2)
        if opt == 1:
            self.data['modo'] = 'FOTO'
            self._advance_to(4)
            return 'Envia la foto o PDF de la factura del taller.'
        self.data['modo'] = 'MANUAL'
        self._advance_to(30)
        return 'Fecha del trabajo? (DD/MM/AA o HOY)'

    # step_4: receive photo/PDF (FOTO mode)
    def step_4(self, message, media_id, mime_type):
        if not media_id:
            return 'Por favor envia la foto o PDF de la factura. O escribe *CANCELAR* para volver.'
        extracted = self._run_vision(media_id, mime_type)
        self.data['vision_data'] = extracted
        self._advance_to(5)
        if extracted:
            return (
                'Datos extraidos de la factura:\n\n'
                f"Fecha: {extracted.get('fecha', '?')}\n"
                f"Taller: {extracted.get('taller', '?')}\n"
                f"CUIT: {extracted.get('cuit', '?')}\n"
                f"Descripcion: {extracted.get('descripcion', '?')}\n"
                f"Repuestos: {extracted.get('repuestos', '?')}\n"
                f"Total: ${extracted.get('total', '?')}\n"
                f"N factura: {extracted.get('nro_factura', '?')}\n\n"
                '1. Confirmar estos datos\n'
                '2. Corregir / carga manual'
            )
        return (
            'No pude leer la factura automaticamente.\n\n'
            '1. Intentar con otro documento\n'
            '2. Carga manual'
        )

    # step_5: confirm/correct vision data
    def step_5(self, message, media_id, mime_type):
        opt = self._parse_int(message, 1, 2)
        if opt is None:
            return self._invalid(2)
        if opt == 1:
            v = self.data.get('vision_data', {})
            self.data.update({
                'fecha': v.get('fecha', ''),
                'taller': v.get('taller', ''),
                'cuit_taller': v.get('cuit', ''),
                'descripcion': v.get('descripcion', ''),
                'repuesto': v.get('repuestos', ''),
                'total': v.get('total'),
                'nro_factura': v.get('nro_factura', ''),
            })
            self._advance_to(6)
            return 'Quien realizo el trabajo?\n\n1. Personal propio\n2. Taller mecanico\n3. Concesionario oficial'
        self.data['modo'] = 'MANUAL'
        self._advance_to(30)
        return 'Fecha del trabajo? (DD/MM/AA o HOY)'

    # step_6: quien realizó
    def step_6(self, message, media_id, mime_type):
        quien = _QUIEN_MAP.get(message.strip())
        if not quien:
            return self._invalid(3)
        self.data['quien_realizo'] = quien
        if quien in ('TALLER', 'CONCESIONARIO'):
            self._advance_to(7)
            return 'Nombre del taller / concesionario:'
        self.data['taller'] = ''
        self._advance_to(8)
        return 'El pago ya fue realizado?\n\n1. Si — registrar pago\n2. No — queda pendiente'

    # step_7: taller name
    def step_7(self, message, media_id, mime_type):
        self.data['taller'] = message.strip()
        self._advance_to(8)
        return 'El pago ya fue realizado?\n\n1. Si — registrar pago\n2. No — queda pendiente'

    # step_8: pago realizado?
    def step_8(self, message, media_id, mime_type):
        opt = self._parse_int(message, 1, 2)
        if opt is None:
            return self._invalid(2)
        self.data['pago_realizado'] = (opt == 1)
        if opt == 1:
            self._advance_to(9)
            return 'Como se pago?\n\n1. Cheque\n2. Transferencia\n3. Tarjeta\n4. Efectivo'
        self.data['metodo_pago'] = ''
        self._advance_to(10)
        return 'Observacion?\n\n1. Si\n2. No'

    # step_9: metodo pago
    def step_9(self, message, media_id, mime_type):
        entry = _PAGO_MAP.get(message.strip())
        if not entry:
            return self._invalid(4)
        self.data['metodo_pago'] = entry[0]
        self._advance_to(10)
        return 'Observacion?\n\n1. Si\n2. No'

    # step_10: observacion y/n
    def step_10(self, message, media_id, mime_type):
        opt = self._parse_int(message, 1, 2)
        if opt is None:
            return self._invalid(2)
        if opt == 1:
            self._advance_to(11)
            return 'Escribi tu observacion:'
        self.data['observacion'] = ''
        self._advance_to(12)
        return self._build_confirmation()

    # step_11: observacion text
    def step_11(self, message, media_id, mime_type):
        self.data['observacion'] = message.strip()
        self._advance_to(12)
        return self._build_confirmation()

    # step_12: final confirmation
    def step_12(self, message, media_id, mime_type):
        opt = self._parse_int(message, 1, 3)
        if opt == 1:
            return self._confirm_save()
        if opt == 2:
            self._restart_flow()
            return self.step_0('', None, None)
        if opt == 3:
            return self._cancel()
        return self._invalid(3)

    # ---- Manual entry steps (30-36) ----

    def step_30(self, message, media_id, mime_type):
        fecha = self._parse_date(message)
        if not fecha:
            return 'Formato incorrecto. Usa DD/MM/AA o escribe HOY.'
        self.data['fecha'] = fecha.isoformat()
        self._advance_to(31)
        return 'Descripcion del trabajo realizado:'

    def step_31(self, message, media_id, mime_type):
        self.data['descripcion'] = message.strip()
        self._advance_to(32)
        return 'Repuesto reemplazado (o escribe - si no hubo):'

    def step_32(self, message, media_id, mime_type):
        self.data['repuesto'] = message.strip().replace('-', '').strip() or ''
        self._advance_to(33)
        return 'Importe total ($):\nEj: 85000\n\nO escribe - si no tenes el monto.'

    def step_33(self, message, media_id, mime_type):
        if message.strip() in ('-', ''):
            self.data['total'] = None
        else:
            val = self._parse_float(message)
            if val is None:
                return 'Ingresa un numero valido o escribe - para omitir.'
            self.data['total'] = val
        # Continue to quien realizó
        self._advance_to(6)
        return 'Quien realizo el trabajo?\n\n1. Personal propio\n2. Taller mecanico\n3. Concesionario oficial'

    def _build_confirmation(self) -> str:
        d = self.data
        pago_str = 'Si' if d.get('pago_realizado') else 'No'
        if d.get('pago_realizado') and d.get('metodo_pago'):
            pago_str = f"Si ({d['metodo_pago'].capitalize()})"
        rows = [
            ('Maquina', d.get('maquinaria_nombre', '-')),
            ('Tipo', _TIPO_DISPLAY.get(d.get('tipo', ''), '-')),
            ('Fecha', d.get('fecha', '-')),
            ('Descripcion', d.get('descripcion', '-')),
            ('Repuesto', d.get('repuesto', '-') or '-'),
            ('Quien realizo', d.get('quien_realizo', '-').replace('_', ' ').capitalize()),
        ]
        if d.get('taller'):
            rows.append(('Taller', d['taller']))
        rows.extend([
            ('Total', f"${d.get('total', '-')}" if d.get('total') else '-'),
            ('N factura', d.get('nro_factura', '-') or '-'),
            ('Pago', pago_str),
        ])
        if d.get('observacion'):
            rows.append(('Observacion', d['observacion']))
        return self._confirmation_block('Confirmar Mantenimiento', rows)

    def _confirm_save(self) -> str:
        d = self.data
        from chatbot.models import RegistroMantenimiento, Maquinaria
        try:
            maquinaria = None
            if d.get('maquinaria_id'):
                maquinaria = Maquinaria.objects.filter(id=d['maquinaria_id']).first()
            fecha = d.get('fecha')
            if not fecha:
                from datetime import date
                fecha = date.today().isoformat()
            RegistroMantenimiento.objects.create(
                maquinaria=maquinaria,
                tipo=d.get('tipo', 'OTRO'),
                fecha=fecha,
                descripcion=d.get('descripcion', ''),
                repuesto=d.get('repuesto', ''),
                quien_realizo=d.get('quien_realizo', ''),
                taller=d.get('taller', ''),
                cuit_taller=d.get('cuit_taller', ''),
                total=d.get('total'),
                nro_factura=d.get('nro_factura', ''),
                pago_realizado=d.get('pago_realizado', False),
                metodo_pago=d.get('metodo_pago', ''),
                observaciones=d.get('observacion', ''),
                cargado_por=self.session.user,
            )
        except Exception as e:
            logger.exception(f'Error saving mantenimiento: {e}')
            return 'Error al guardar. Por favor intenta de nuevo.'

        return (
            f"Mantenimiento registrado para {d.get('maquinaria_nombre', 'la maquina')}.\n\n"
            'Escribi *MENU* para volver al inicio.'
        )

    def _run_vision(self, media_id: str, mime_type: str) -> dict:
        try:
            from chatbot.services.whatsapp import WhatsAppService
            from chatbot.services.claude_vision import ClaudeVisionService
            wa = WhatsAppService()
            media_url = wa.get_media_url(media_id)
            if not media_url:
                return {}
            file_bytes = wa.download_media(media_url)
            if not file_bytes:
                return {}
            vision = ClaudeVisionService()
            return vision.analyze_factura_mantenimiento(file_bytes, mime_type or 'image/jpeg')
        except Exception as e:
            logger.exception(f'Mantenimiento vision error: {e}')
            return {}
