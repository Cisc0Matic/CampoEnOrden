def show_main_menu(user):
    if not user:
        return (
            'Tu numero no esta registrado en Campo en Orden.\n'
            'Contacta a tu asesor para que te habilite el acceso.\n\n'
            'O escribe HOLA para intentar de nuevo.'
        )

    nombre = user.first_name or user.username
    role = user.role

    if role in ('ADMIN_PRINCIPAL', 'ADMIN_EMPRESA', 'PRODUCTOR'):
        return {
            'body': f'Hola *{nombre}*, bienvenido a Campo en Orden.\nQue querés hacer hoy?',
            'header': 'Menú Principal',
            'button_text': 'Ver opciones',
            'sections': [
                {
                    'title': 'Gestión',
                    'rows': [
                        {'id': '1', 'title': 'Campos'},
                        {'id': '2', 'title': 'Labores'},
                        {'id': '3', 'title': 'ABM de Insumos'},
                        {'id': '4', 'title': 'Transporte de granos'},
                        {'id': '5', 'title': 'Comercialización de granos'},
                        {'id': '6', 'title': 'Informes'},
                        {'id': '7', 'title': 'Maquinaria y Rodados'},
                    ],
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
        return {
            'body': f'Hola *{nombre}*, que querés hacer hoy?',
            'header': 'Menú Principal',
            'button_text': 'Ver opciones',
            'sections': [
                {
                    'title': 'Opciones',
                    'rows': [
                        {'id': '1', 'title': 'Labores'},
                        {'id': '2', 'title': 'Combustible'},
                        {'id': '3', 'title': 'Mantenimiento'},
                    ],
                },
            ],
        }

    if role == 'CONSULTA':
        return {
            'body': f'Hola *{nombre}*, que querés ver?',
            'header': 'Menú',
            'button_text': 'Ver opciones',
            'sections': [
                {
                    'title': 'Opciones',
                    'rows': [
                        {'id': '1', 'title': 'Informes'},
                    ],
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
