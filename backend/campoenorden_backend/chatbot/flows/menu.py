_ROLE_LABELS = {
    'ADMIN_PRINCIPAL': 'Admin Principal',
    'ADMIN_EMPRESA': 'Admin de Empresa',
    'PRODUCTOR': 'Productor',
    'OPERARIO': 'Operario',
    'CONSULTA': 'Consulta',
}


def _resume_row(session):
    if not session:
        return None
    resume = (session.session_data or {}).get('_resume')
    if not resume:
        return None
    from chatbot.flows import FLOW_LABELS
    label = FLOW_LABELS.get(resume.get('flow'))
    if not label:
        return None
    return {'id': 'RETOMAR', 'title': f'🔁 Retomar carga de {label}'}


def _greeting(user) -> str:
    nombre = user.first_name or user.username
    role = user.role
    rol_label = _ROLE_LABELS.get(role, user.get_role_display() or role)
    empresa = user.empresa.nombre if user.empresa_id and user.empresa else ''
    line = f'Hola *{nombre}* ({rol_label})'
    if empresa:
        line += f' · {empresa}'
    return line


def show_main_menu(user, session=None):
    if not user:
        return (
            'Tu numero no esta registrado en Campo en Orden.\n'
            'Contacta a tu asesor para que te habilite el acceso.\n\n'
            'O escribe HOLA para intentar de nuevo.'
        )

    nombre = user.first_name or user.username
    role = user.role
    greeting = _greeting(user)
    resume = _resume_row(session)

    if role in ('ADMIN_PRINCIPAL', 'ADMIN_EMPRESA', 'PRODUCTOR'):
        rows = [
            {'id': '1', 'title': 'Campos'},
            {'id': '2', 'title': 'Labores'},
            {'id': '3', 'title': 'ABM de Insumos'},
            {'id': '4', 'title': 'Transporte de granos'},
            {'id': '5', 'title': 'Comercialización de granos'},
            {'id': '6', 'title': 'Informes'},
            {'id': '7', 'title': 'Maquinaria y Rodados'},
        ]
        if resume:
            rows.insert(0, resume)
        return {
            'body': f'{greeting}.\n¿Qué querés hacer hoy?',
            'header': 'Menú Principal',
            'button_text': 'Ver opciones',
            'sections': [
                {
                    'title': 'Gestión',
                    'rows': rows,
                },
                {
                    'title': 'Consultas',
                    'rows': [
                        {'id': '8', 'title': 'Precios de cereales'},
                        {'id': '9', 'title': 'Dólar y tipo de cambio'},
                        {'id': '10', 'title': 'Clima y pronóstico'},
                        {'id': '11', 'title': 'Hablar con mi asesor'},
                    ],
                },
            ],
        }

    if role == 'OPERARIO':
        rows = [
            {'id': '1', 'title': 'Labores'},
            {'id': '2', 'title': 'Combustible'},
            {'id': '3', 'title': 'Mantenimiento'},
        ]
        if resume:
            rows.insert(0, resume)
        return {
            'body': f'{greeting}.\n¿Qué querés hacer hoy?',
            'header': 'Menú Principal',
            'button_text': 'Ver opciones',
            'sections': [
                {
                    'title': 'Opciones',
                    'rows': rows,
                },
            ],
        }

    if role == 'CONSULTA':
        rows = [
            {'id': '1', 'title': 'Informes'},
        ]
        if resume:
            rows.insert(0, resume)
        return {
            'body': f'{greeting}.\n¿Qué querés ver?',
            'header': 'Menú',
            'button_text': 'Ver opciones',
            'sections': [
                {
                    'title': 'Opciones',
                    'rows': rows,
                },
            ],
        }

    return f'Hola *{nombre}*, tu perfil no tiene acceso al chatbot. Contacta a tu asesor.'


def get_labores_submenu():
    return {
        'body': '*Labores* — Que tipo de labor?',
        'button_text': 'Ver labores',
        'sections': [
            {
                'title': 'Labores',
                'rows': [
                    {'id': '1', 'title': 'Pulverización'},
                    {'id': '2', 'title': 'Fertilización'},
                    {'id': '3', 'title': 'Siembra'},
                    {'id': '4', 'title': 'Cosecha'},
                ],
            },
            {
                'title': 'Navegación',
                'rows': [
                    {'id': 'GO_MENU', 'title': '📋 Menú principal'},
                ],
            },
        ],
    }


def get_campos_submenu():
    return {
        'body': '*Campos* — ¿Qué querés hacer?',
        'button_text': 'Ver opciones',
        'sections': [
            {
                'title': 'Consultas',
                'rows': [
                    {'id': 'CAMPOS_VER', 'title': 'Ver mis campos'},
                    {'id': 'CAMPOS_LOTES', 'title': 'Ver lotes de un campo'},
                ],
            },
            {
                'title': 'Gestión (próximamente)',
                'rows': [
                    {'id': 'CAMPOS_ALTA', 'title': 'Dar de alta un campo'},
                    {'id': 'CAMPOS_CONTRATO', 'title': 'Contratos de arrendamiento'},
                    {'id': 'CAMPOS_ALQUILER', 'title': 'Registrar pago de alquiler'},
                ],
            },
            {
                'title': 'Navegación',
                'rows': [
                    {'id': 'GO_MENU', 'title': '📋 Menú principal'},
                ],
            },
        ],
    }


def get_maquinaria_submenu():
    return {
        'body': '*Maquinaria y Rodados*',
        'button_text': 'Ver opciones',
        'sections': [
            {
                'title': 'Maquinaria',
                'rows': [
                    {'id': '1', 'title': 'Inventario de maquinaria'},
                    {'id': '2', 'title': 'Combustible'},
                    {'id': '3', 'title': 'Mantenimiento'},
                ],
            },
            {
                'title': 'Navegación',
                'rows': [
                    {'id': 'GO_MENU', 'title': '📋 Menú principal'},
                ],
            },
        ],
    }
