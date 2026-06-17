def show_main_menu(user) -> str:
    if not user:
        return (
            'Tu numero no esta registrado en Campo en Orden.\n'
            'Contacta a tu asesor para que te habilite el acceso.\n\n'
            'O escribe HOLA para intentar de nuevo.'
        )

    nombre = user.first_name or user.username
    role = user.role

    if role in ('ADMIN_PRINCIPAL', 'ADMIN_EMPRESA', 'PRODUCTOR'):
        return (
            f'Hola *{nombre}*, bienvenido a Campo en Orden.\n'
            'Que queris hacer hoy?\n\n'
            '1. Campos\n'
            '2. Labores\n'
            '3. ABM de Insumos\n'
            '4. Transporte de granos\n'
            '5. Comercializacion de granos\n'
            '6. Informes\n'
            '7. Maquinaria y Rodados\n'
            '8. Precios de cereales\n'
            '9. Dolar y tipo de cambio\n'
            '10. Clima y pronostico\n'
            '11. Hablar con mi asesor'
        )

    if role == 'OPERARIO':
        return (
            f'Hola *{nombre}*, que queris hacer hoy?\n\n'
            '1. Labores\n'
            '2. Combustible\n'
            '3. Mantenimiento'
        )

    if role == 'CONSULTA':
        return (
            f'Hola *{nombre}*, que queris ver?\n\n'
            '1. Informes'
        )

    return f'Hola *{nombre}*, tu perfil no tiene acceso al chatbot. Contacta a tu asesor.'


def get_labores_submenu() -> str:
    return (
        '*Labores* — Que tipo de labor?\n\n'
        '1. Pulverizacion\n'
        '2. Fertilizacion\n'
        '3. Siembra\n'
        '4. Cosecha\n\n'
        'O escribe *MENU* para volver.'
    )


def get_maquinaria_submenu() -> str:
    return (
        '*Maquinaria y Rodados*\n\n'
        '1. Inventario de maquinaria\n'
        '2. Combustible\n'
        '3. Mantenimiento\n\n'
        'O escribe *MENU* para volver.'
    )
