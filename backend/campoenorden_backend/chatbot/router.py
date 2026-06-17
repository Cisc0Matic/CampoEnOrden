import logging

from .flows import FLOW_REGISTRY, get_flow_class, start_flow
from .flows.menu import show_main_menu, get_labores_submenu, get_maquinaria_submenu
from users.models import User

logger = logging.getLogger(__name__)

_RESET_WORDS = {'MENU', 'INICIO', 'HOLA', '/START', 'START'}


def handle_message_router(session, text: str, media_id: str, mime_type: str, wa_service) -> str:
    user = session.user
    flow = session.current_flow
    msg = (text or '').strip()
    upper = msg.upper()

    # DNI identification
    if session.session_data.get('awaiting_dni'):
        return _handle_dni_input(session, msg)

    # Global reset
    if upper in _RESET_WORDS:
        session.current_flow = ''
        session.current_step = 0
        session.session_data = {}
        session.user = None
        session.save(update_fields=['current_flow', 'current_step', 'session_data', 'user', 'last_activity'])
        session.session_data['awaiting_dni'] = True
        session.save(update_fields=['session_data'])
        return (
            'Bienvenido a Campo en Orden.\n'
            'Por favor, ingresá tu DNI para identificarte:'
        )

    # Active data-entry flow
    if flow and flow in FLOW_REGISTRY:
        FlowClass = get_flow_class(flow)
        return FlowClass(session, wa_service).handle(msg, media_id, mime_type)

    # Sub-menu navigation flows
    if flow == 'labores_menu':
        return _handle_labores_menu(session, msg, wa_service)
    if flow == 'maquinaria_menu':
        return _handle_maquinaria_menu(session, msg, wa_service)

    # No active flow → main menu navigation
    return _handle_main_menu_nav(session, msg, user, wa_service)


def _handle_main_menu_nav(session, message: str, user, wa_service) -> str:
    if not user:
        return show_main_menu(None)

    role = user.role
    is_admin = role in ('ADMIN_PRINCIPAL', 'ADMIN_EMPRESA', 'PRODUCTOR')

    if is_admin:
        opt = _try_int(message, 1, 11)
        if opt == 1:
            return 'Modulo de Campos (proximamente disponible).\n\nEscribi *MENU* para volver.'
        if opt == 2:
            return _enter_labores_menu(session)
        if opt == 3:
            return 'Modulo de ABM de Insumos (proximamente disponible).\n\nEscribi *MENU* para volver.'
        if opt == 4:
            return 'Modulo de Transporte de Granos (proximamente disponible).\n\nEscribi *MENU* para volver.'
        if opt == 5:
            return 'Modulo de Comercializacion (proximamente disponible).\n\nEscribi *MENU* para volver.'
        if opt == 6:
            return 'Modulo de Informes (proximamente disponible).\n\nEscribi *MENU* para volver.'
        if opt == 7:
            return _enter_maquinaria_menu(session)
        if opt == 8:
            return _get_precios_cereales()
        if opt == 9:
            return _get_dolar()
        if opt == 10:
            return _get_clima()
        if opt == 11:
            return 'Hablar con tu asesor (proximamente disponible).\n\nEscribi *MENU* para volver.'
        return f'Opcion no valida. Escribi un numero del 1 al 11.\n\n{show_main_menu(user)}'

    if role == 'OPERARIO':
        opt = _try_int(message, 1, 3)
        if opt == 1:
            return _enter_labores_menu(session)
        if opt == 2:
            return start_flow(session, 'combustible', wa_service)
        if opt == 3:
            return start_flow(session, 'mantenimiento', wa_service)
        return f'Opcion no valida. Escribi un numero del 1 al 3.\n\n{show_main_menu(user)}'

    if role == 'CONSULTA':
        opt = _try_int(message, 1, 1)
        if opt == 1:
            return 'Modulo de Informes (proximamente disponible).\n\nEscribi *MENU* para volver.'
        return 'Opcion no valida. Escribi 1 para ver informes.'

    return show_main_menu(user)


def _handle_dni_input(session, dni_input: str) -> str:
    dni = dni_input.strip()
    if not dni:
        return 'Por favor, ingresá tu DNI:'

    user = User.objects.filter(dni=dni).first()
    if not user:
        return (
            'DNI no encontrado en el sistema.\n'
            'Verificá el número o contactá a tu asesor.\n'
            'Escribí *MENU* para salir.'
        )

    if not user.is_active:
        return (
            'Tu usuario está desactivado.\n'
            'Contactá a tu asesor para reactivarlo.\n'
            'Escribí *MENU* para salir.'
        )

    session.user = user
    session.session_data.pop('awaiting_dni', None)
    session.save(update_fields=['user', 'session_data', 'last_activity'])
    return show_main_menu(user)


def _enter_labores_menu(session) -> str:
    session.current_flow = 'labores_menu'
    session.current_step = 0
    session.session_data = {}
    session.save(update_fields=['current_flow', 'current_step', 'session_data', 'last_activity'])
    return get_labores_submenu()


def _enter_maquinaria_menu(session) -> str:
    session.current_flow = 'maquinaria_menu'
    session.current_step = 0
    session.session_data = {}
    session.save(update_fields=['current_flow', 'current_step', 'session_data', 'last_activity'])
    return get_maquinaria_submenu()


def _handle_labores_menu(session, message: str, wa_service) -> str:
    opt = _try_int(message, 1, 4)
    flows = {1: 'pulverizacion', 2: 'fertilizacion', 3: 'siembra', 4: 'cosecha'}
    if opt in flows:
        return start_flow(session, flows[opt], wa_service)
    return f'Opcion no valida. Escribi un numero del 1 al 4.\n\n{get_labores_submenu()}'


def _handle_maquinaria_menu(session, message: str, wa_service) -> str:
    opt = _try_int(message, 1, 3)
    if opt == 1:
        return 'Modulo de Inventario de Maquinaria (proximamente disponible).\n\nEscribi *MENU* para volver.'
    if opt == 2:
        return start_flow(session, 'combustible', wa_service)
    if opt == 3:
        return start_flow(session, 'mantenimiento', wa_service)
    return f'Opcion no valida. Escribi un numero del 1 al 3.\n\n{get_maquinaria_submenu()}'


def _try_int(message: str, min_val: int, max_val: int):
    try:
        v = int((message or '').strip())
        if min_val <= v <= max_val:
            return v
    except (ValueError, TypeError):
        pass
    return None


def _get_precios_cereales() -> str:
    return (
        'Precios BCR (integracion en desarrollo).\n\n'
        'Pronto vas a poder consultar precios de soja, maiz, trigo y girasol en tiempo real.\n\n'
        'Escribi *MENU* para volver.'
    )


def _get_dolar() -> str:
    return (
        'Dolar y tipo de cambio (integracion en desarrollo).\n\n'
        'Escribi *MENU* para volver.'
    )


def _get_clima() -> str:
    return (
        'Clima y pronostico (integracion en desarrollo).\n\n'
        'Pronto vas a poder ver el pronostico por coordenadas de tu campo.\n\n'
        'Escribi *MENU* para volver.'
    )
