import logging

from .flows import FLOW_REGISTRY, get_flow_class, start_flow, stash_active_flow, pop_resume, FLOW_LABELS
from .flows.menu import show_main_menu, get_labores_submenu, get_maquinaria_submenu, get_campos_submenu
from .flows.base import BaseFlow

logger = logging.getLogger(__name__)

_RESET_WORDS = {'MENU', 'INICIO', 'HOLA', '/START', 'START'}


def handle_message_router(session, text: str, media_id: str, mime_type: str, wa_service) -> str:
    user = session.user
    flow = session.current_flow
    msg = (text or '').strip()
    upper = msg.upper()

    # GO_MENU / global reset — keep user, just return to main menu.
    # Si hay un flujo de carga en curso se guarda para poder retomarlo.
    if upper in _RESET_WORDS or upper == 'GO_MENU':
        if flow and flow in FLOW_REGISTRY:
            stash_active_flow(session)
        else:
            session.session_data = {}
        session.current_flow = ''
        session.current_step = 0
        session.save(update_fields=['current_flow', 'current_step', 'session_data', 'last_activity'])
        return show_main_menu(session.user, session)

    # Active data-entry flow
    if flow and flow in FLOW_REGISTRY:
        FlowClass = get_flow_class(flow)
        return FlowClass(session, wa_service).handle(msg, media_id, mime_type)

    # Sub-menu navigation flows
    if flow == 'labores_menu':
        return _handle_labores_menu(session, msg, wa_service)
    if flow == 'maquinaria_menu':
        return _handle_maquinaria_menu(session, msg, wa_service)
    if flow == 'campos_menu':
        return _handle_campos_menu(session, msg, wa_service)

    # No active flow → main menu navigation
    return _handle_main_menu_nav(session, msg, user, wa_service)


def _handle_main_menu_nav(session, message: str, user, wa_service) -> str:
    if not user:
        return show_main_menu(None)

    upper = (message or '').strip().upper()
    if upper == 'RETOMAR':
        return _handle_resume(session, wa_service)

    role = user.role
    is_admin = role in ('ADMIN_PRINCIPAL', 'ADMIN_EMPRESA', 'PRODUCTOR')

    if is_admin:
        opt = _try_int(message, 1, 11)
        if opt == 1:
            return _enter_campos_menu(session)
        if opt == 2:
            return _enter_labores_menu(session)
        if opt == 3:
            return BaseFlow._with_menu('Módulo de ABM de Insumos — próximamente disponible.')
        if opt == 4:
            return BaseFlow._with_menu('Módulo de Transporte de Granos — próximamente disponible.')
        if opt == 5:
            return BaseFlow._with_menu('Módulo de Comercialización de Granos — próximamente disponible.')
        if opt == 6:
            return BaseFlow._with_menu('Módulo de Informes — próximamente disponible.')
        if opt == 7:
            return _enter_maquinaria_menu(session)
        if opt == 8:
            return _get_precios_cereales()
        if opt == 9:
            return _get_dolar()
        if opt == 10:
            return _get_clima()
        if opt == 11:
            return BaseFlow._with_menu('Hablar con tu asesor — próximamente disponible.')
        return BaseFlow._with_menu('Opción no válida. Seleccioná un número del 1 al 11 del menú que aparece abajo.')

    if role == 'OPERARIO':
        opt = _try_int(message, 1, 3)
        if opt == 1:
            return _enter_labores_menu(session)
        if opt == 2:
            return start_flow(session, 'combustible', wa_service)
        if opt == 3:
            return start_flow(session, 'mantenimiento', wa_service)
        return BaseFlow._with_menu('Opción no válida. Seleccioná un número del 1 al 3 del menú que aparece abajo.')

    if role == 'CONSULTA':
        opt = _try_int(message, 1, 1)
        if opt == 1:
            return BaseFlow._with_menu('Módulo de Informes — próximamente disponible.')
        return BaseFlow._with_menu('Opción no válida. Escribí 1 para ver informes.')

    return show_main_menu(user, session)


# ── Retomar carga pendiente ───────────────────────────────────────────────────

def _handle_resume(session, wa_service) -> dict:
    resume = (session.session_data or {}).get('_resume')
    if not resume or resume.get('flow') not in FLOW_REGISTRY:
        pop_resume(session)
        return BaseFlow._with_menu('No hay ninguna carga pendiente por retomar.')

    flow_name = resume['flow']
    session.current_flow = flow_name
    session.current_step = resume.get('step', 0)
    session.session_data.pop('_resume', None)
    session.save(update_fields=['current_flow', 'current_step', 'session_data', 'last_activity'])

    prompt = (resume.get('prompt') or '').strip()
    if not prompt:
        from chatbot.models import WhatsAppMessage
        last_out = WhatsAppMessage.objects.filter(
            session=session, direction=WhatsAppMessage.DIRECTION_OUT
        ).order_by('-id').first()
        prompt = (last_out.content or '').strip() if last_out else ''
    if not prompt:
        prompt = 'Continuá desde donde quedaste.'

    label = FLOW_LABELS.get(flow_name, flow_name)
    return {
        'body': (
            f'🔁 Retomamos la carga de *{label}*.\n\n'
            f'📌 {prompt}\n\n'
            'Respondé con la opción correspondiente o escribí *MENU* para volver.'
        ),
        'buttons': [
            {'type': 'reply', 'reply': {'id': 'MENU', 'title': '📋 Menú principal'}},
        ],
    }


# ── Campos menu ───────────────────────────────────────────────────────────────

def _enter_campos_menu(session) -> dict:
    session.current_flow = 'campos_menu'
    session.current_step = 0
    session.session_data = {}
    session.save(update_fields=['current_flow', 'current_step', 'session_data', 'last_activity'])
    return get_campos_submenu()


def _handle_campos_menu(session, message: str, wa_service) -> str:
    upper = (message or '').strip().upper()

    if upper == 'CAMPOS_VER':
        from .flows.campos import ver_todos_los_campos
        session.current_flow = ''
        session.save(update_fields=['current_flow', 'last_activity'])
        text = ver_todos_los_campos(session)
        if not text:
            return BaseFlow._with_menu('No hay campos registrados en el sistema.')
        return BaseFlow._with_menu(text)

    if upper == 'CAMPOS_LOTES':
        return start_flow(session, 'campos_lotes', wa_service)

    if upper in ('CAMPOS_ALTA', 'CAMPOS_CONTRATO', 'CAMPOS_ALQUILER'):
        return BaseFlow._with_menu('Esta función está en desarrollo. Pronto disponible.')

    return BaseFlow._with_menu('Opción no reconocida. Usá el menú de arriba.')


# ── Labores menu ──────────────────────────────────────────────────────────────

def _enter_labores_menu(session) -> str:
    session.current_flow = 'labores_menu'
    session.current_step = 0
    session.session_data = {}
    session.save(update_fields=['current_flow', 'current_step', 'session_data', 'last_activity'])
    return get_labores_submenu()


def _handle_labores_menu(session, message: str, wa_service) -> str:
    opt = _try_int(message, 1, 4)
    flows = {1: 'pulverizacion', 2: 'fertilizacion', 3: 'siembra', 4: 'cosecha'}
    if opt in flows:
        return start_flow(session, flows[opt], wa_service)
    return BaseFlow._with_menu('Opción no válida. Seleccioná un número del 1 al 4 del menú que aparece abajo.')


# ── Maquinaria menu ───────────────────────────────────────────────────────────

def _enter_maquinaria_menu(session) -> str:
    session.current_flow = 'maquinaria_menu'
    session.current_step = 0
    session.session_data = {}
    session.save(update_fields=['current_flow', 'current_step', 'session_data', 'last_activity'])
    return get_maquinaria_submenu()


def _handle_maquinaria_menu(session, message: str, wa_service) -> str:
    opt = _try_int(message, 1, 3)
    if opt == 1:
        return start_flow(session, 'maquinaria_inventario', wa_service)
    if opt == 2:
        return start_flow(session, 'combustible', wa_service)
    if opt == 3:
        return start_flow(session, 'mantenimiento', wa_service)
    return BaseFlow._with_menu('Opción no válida. Seleccioná un número del 1 al 3 del menú que aparece abajo.')


# ── External data ─────────────────────────────────────────────────────────────

def _get_precios_cereales() -> dict:
    from .services.external_apis import get_precios_cereales_text
    text = get_precios_cereales_text()
    return BaseFlow._with_menu(text)


def _get_dolar() -> dict:
    from .services.external_apis import get_dolar_text
    text = get_dolar_text()
    return BaseFlow._with_menu(text)


def _get_clima() -> dict:
    return BaseFlow._with_menu(
        'Clima y pronóstico — integración en desarrollo.\n\n'
        'Pronto vas a poder ver el pronóstico por coordenadas de tu campo.'
    )


# ── Helpers ───────────────────────────────────────────────────────────────────

def _try_int(message: str, min_val: int, max_val: int):
    try:
        v = int((message or '').strip())
        if min_val <= v <= max_val:
            return v
    except (ValueError, TypeError):
        pass
    return None
