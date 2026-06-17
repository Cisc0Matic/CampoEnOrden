import logging

from .base import BaseFlow

logger = logging.getLogger(__name__)


class CombustibleFlow(BaseFlow):
    FLOW_NAME = 'combustible'

    # step_0: ask for photo or MANUAL
    def step_0(self, message, media_id, mime_type):
        self.data = {}
        self._advance_to(1)
        return (
            'Envia la foto del remito o PDF de la factura de combustible.\n\n'
            'O escribe *MANUAL* para carga manual de datos.'
        )

    # step_1: receive photo/PDF or MANUAL text
    def step_1(self, message, media_id, mime_type):
        if message.strip().upper() == 'MANUAL':
            self.data['modo'] = 'MANUAL'
            self._advance_to(20)
            return 'Fecha del remito/factura? (DD/MM/AA o HOY)'

        if media_id:
            extracted = self._run_vision(media_id, mime_type)
            self.data.update({'modo': 'FOTO', 'vision_data': extracted})
            self._advance_to(2)
            if extracted:
                return (
                    'Datos extraidos del documento:\n\n'
                    f"Fecha: {extracted.get('fecha', '?')}\n"
                    f"Proveedor: {extracted.get('proveedor', '?')}\n"
                    f"CUIT: {extracted.get('cuit', '?')}\n"
                    f"Litros: {extracted.get('litros', '?')}\n"
                    f"Precio/litro: {extracted.get('precio_litro', '?')}\n"
                    f"Total: ${extracted.get('total', '?')}\n"
                    f"N documento: {extracted.get('nro_documento', '?')}\n\n"
                    '1. Confirmar estos datos\n'
                    '2. Corregir / carga manual'
                )
            return (
                'No pude leer el documento automaticamente.\n\n'
                '1. Intentar con otro documento\n'
                '2. Carga manual'
            )

        return (
            'No recibi ninguna imagen o archivo.\n\n'
            'Envia la foto/PDF o escribe *MANUAL* para carga manual.'
        )

    # step_2: confirm/correct vision data
    def step_2(self, message, media_id, mime_type):
        opt = self._parse_int(message, 1, 2)
        if opt is None:
            return self._invalid(2)
        if opt == 1:
            v = self.data.get('vision_data', {})
            self.data.update({
                'fecha': v.get('fecha', ''),
                'proveedor': v.get('proveedor', ''),
                'cuit_proveedor': v.get('cuit', ''),
                'litros': v.get('litros'),
                'precio_litro': v.get('precio_litro'),
                'total': v.get('total'),
                'nro_documento': v.get('nro_documento', ''),
            })
            self._advance_to(3)
            return self._ask_maquinaria()
        # Manual entry
        self.data['modo'] = 'MANUAL'
        self._advance_to(20)
        return 'Fecha del remito/factura? (DD/MM/AA o HOY)'

    # step_3: select maquina
    def step_3(self, message, media_id, mime_type):
        maquinaria = self._get_maquinaria()
        if not maquinaria:
            self.data.update({'maquinaria_id': None, 'maquinaria_nombre': 'Sin inventario'})
            self._advance_to(4)
            return self._ask_campo()
        n = self._parse_int(message, 1, len(maquinaria))
        if n is None:
            return self._invalid(len(maquinaria))
        m = maquinaria[n - 1]
        self.data.update({'maquinaria_id': m.id, 'maquinaria_nombre': m.nombre})
        self._advance_to(4)
        return self._ask_campo()

    # step_4: select campo
    def step_4(self, message, media_id, mime_type):
        if message.strip().upper() == 'VARIOS':
            self.data.update({'campo_id': None, 'campo_nombre': 'Varios'})
            self._advance_to(5)
            return 'Observacion?\n\n1. Si\n2. No'
        campos = self._get_campos()
        if not campos:
            self.data.update({'campo_id': None, 'campo_nombre': '-'})
            self._advance_to(5)
            return 'Observacion?\n\n1. Si\n2. No'
        n = self._parse_int(message, 1, len(campos))
        if n is None:
            return self._invalid(len(campos))
        c = campos[n - 1]
        self.data.update({'campo_id': c.id, 'campo_nombre': c.nombre})
        self._advance_to(5)
        return 'Observacion?\n\n1. Si\n2. No'

    # step_5: observacion y/n
    def step_5(self, message, media_id, mime_type):
        opt = self._parse_int(message, 1, 2)
        if opt is None:
            return self._invalid(2)
        if opt == 1:
            self._advance_to(6)
            return 'Escribi tu observacion:'
        self.data['observacion'] = ''
        self._advance_to(7)
        return self._build_confirmation()

    # step_6: observacion text
    def step_6(self, message, media_id, mime_type):
        self.data['observacion'] = message.strip()
        self._advance_to(7)
        return self._build_confirmation()

    # step_7: final confirmation
    def step_7(self, message, media_id, mime_type):
        opt = self._parse_int(message, 1, 3)
        if opt == 1:
            return self._confirm_save()
        if opt == 2:
            self._restart_flow()
            return self.step_0('', None, None)
        if opt == 3:
            return self._cancel()
        return self._invalid(3)

    # ---- Manual entry steps (20-26) ----

    def step_20(self, message, media_id, mime_type):
        fecha = self._parse_date(message)
        if not fecha:
            return 'Formato incorrecto. Usa DD/MM/AA o escribe HOY.'
        self.data['fecha'] = fecha.isoformat()
        self._advance_to(21)
        return 'Proveedor (nombre de la empresa o persona):'

    def step_21(self, message, media_id, mime_type):
        self.data['proveedor'] = message.strip()
        self._advance_to(22)
        return 'Litros cargados:\nEj: 500'

    def step_22(self, message, media_id, mime_type):
        val = self._parse_float(message)
        if val is None:
            return 'Ingresa un numero valido (Ej: 500).'
        self.data['litros'] = val
        self._advance_to(23)
        return 'Total de la factura/remito ($):\nEj: 350000'

    def step_23(self, message, media_id, mime_type):
        val = self._parse_float(message)
        if val is None:
            return 'Ingresa un numero valido.'
        self.data['total'] = val
        self._advance_to(24)
        return 'Numero de remito/factura (o escribe - si no tenes):'

    def step_24(self, message, media_id, mime_type):
        self.data['nro_documento'] = message.strip().replace('-', '').strip() or ''
        # Go to maquina selection
        self._advance_to(3)
        return self._ask_maquinaria()

    def _ask_maquinaria(self) -> str:
        maquinaria = self._get_maquinaria()
        if not maquinaria:
            self.data.update({'maquinaria_id': None, 'maquinaria_nombre': 'Sin inventario'})
            self._advance_to(4)
            return self._ask_campo_text()
        opts = '\n'.join(f'{i+1}. {m.nombre} ({m.tipo})' for i, m in enumerate(maquinaria))
        return f'A que maquina?\n\n{opts}'

    def _ask_campo(self) -> str:
        return self._ask_campo_text()

    def _ask_campo_text(self) -> str:
        campos = self._get_campos()
        if not campos:
            self.data.update({'campo_id': None, 'campo_nombre': '-'})
            self._advance_to(5)
            return 'Observacion?\n\n1. Si\n2. No'
        opts = '\n'.join(f'{i+1}. {c.nombre}' for i, c in enumerate(campos))
        self.data['campos_ids'] = [c.id for c in campos]
        return f'A que campo?\n\n{opts}\n\nO escribe *VARIOS* si fue para varios campos.'

    def _build_confirmation(self) -> str:
        d = self.data
        rows = [
            ('Fecha', d.get('fecha', '-')),
            ('Proveedor', d.get('proveedor', '-')),
            ('Litros', str(d.get('litros', '-'))),
            ('Total', f"${d.get('total', '-')}"),
            ('N documento', d.get('nro_documento', '-') or '-'),
            ('Maquina', d.get('maquinaria_nombre', '-')),
            ('Campo', d.get('campo_nombre', '-')),
        ]
        if d.get('observacion'):
            rows.append(('Observacion', d['observacion']))
        return self._confirmation_block('Confirmar Carga de Combustible', rows)

    def _confirm_save(self) -> str:
        d = self.data
        from chatbot.models import RegistroCombustible, Maquinaria
        from core.models import Campo
        try:
            maquinaria = None
            if d.get('maquinaria_id'):
                maquinaria = Maquinaria.objects.filter(id=d['maquinaria_id']).first()
            campo = None
            if d.get('campo_id'):
                campo = Campo.objects.filter(id=d['campo_id']).first()
            fecha = d.get('fecha')
            if not fecha:
                from datetime import date
                fecha = date.today().isoformat()
            RegistroCombustible.objects.create(
                maquinaria=maquinaria,
                campo=campo,
                fecha=fecha,
                proveedor=d.get('proveedor', ''),
                cuit_proveedor=d.get('cuit_proveedor', ''),
                litros=d.get('litros'),
                precio_litro=d.get('precio_litro'),
                total=d.get('total'),
                nro_documento=d.get('nro_documento', ''),
                observaciones=d.get('observacion', ''),
                cargado_por=self.session.user,
            )
        except Exception as e:
            logger.exception(f'Error saving combustible: {e}')
            return 'Error al guardar. Por favor intenta de nuevo.'

        return (
            'Combustible registrado correctamente.\n\n'
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
            return vision.analyze_factura_combustible(file_bytes, mime_type or 'image/jpeg')
        except Exception as e:
            logger.exception(f'Combustible vision error: {e}')
            return {}
