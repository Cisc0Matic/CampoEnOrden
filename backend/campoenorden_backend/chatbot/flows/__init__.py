from .pulverizacion import PulverizacionFlow
from .fertilizacion import FertilizacionFlow
from .siembra import SiembraFlow
from .cosecha import CosechaFlow
from .combustible import CombustibleFlow
from .mantenimiento import MantenimientoFlow
from .campos import CamposFlow
from .maquinaria_inventario import MaquinariaInventarioFlow

FLOW_REGISTRY = {
    'pulverizacion': PulverizacionFlow,
    'fertilizacion': FertilizacionFlow,
    'siembra': SiembraFlow,
    'cosecha': CosechaFlow,
    'combustible': CombustibleFlow,
    'mantenimiento': MantenimientoFlow,
    'campos_lotes': CamposFlow,
    'maquinaria_inventario': MaquinariaInventarioFlow,
}

FLOW_LABELS = {
    'pulverizacion': 'Pulverización',
    'fertilizacion': 'Fertilización',
    'siembra': 'Siembra',
    'cosecha': 'Cosecha',
    'combustible': 'Combustible',
    'mantenimiento': 'Mantenimiento',
    'campos_lotes': 'Lotes de campo',
    'maquinaria_inventario': 'Inventario de maquinaria',
}

RESUME_KEY = '_resume'


def get_flow_class(name: str):
    return FLOW_REGISTRY.get(name)


def stash_active_flow(session) -> bool:
    """Guarda el flujo de carga en curso para poder retomarlo desde el menú."""
    if session.current_flow not in FLOW_REGISTRY:
        return False
    data = session.session_data or {}
    has_progress = session.current_step > 0 or any(k != RESUME_KEY for k in data)
    if not has_progress:
        return False
    # Última pregunta que el bot le hizo al usuario dentro del flujo
    prompt = ''
    try:
        from chatbot.models import WhatsAppMessage
        last_out = WhatsAppMessage.objects.filter(
            session=session, direction=WhatsAppMessage.DIRECTION_OUT
        ).order_by('-id').first()
        if last_out and last_out.content:
            prompt = last_out.content.strip()
    except Exception:
        pass
    data[RESUME_KEY] = {'flow': session.current_flow, 'step': session.current_step, 'prompt': prompt}
    return True


def pop_resume(session) -> dict | None:
    data = session.session_data or {}
    resume = data.pop(RESUME_KEY, None) or None
    session.save(update_fields=['session_data', 'last_activity'])
    return resume


def start_flow(session, flow_name: str, wa_service) -> str:
    FlowClass = FLOW_REGISTRY.get(flow_name)
    if not FlowClass:
        return 'Modulo no disponible.'
    session.current_flow = flow_name
    session.current_step = 0
    session.session_data = {}
    session.save(update_fields=['current_flow', 'current_step', 'session_data', 'last_activity'])
    flow = FlowClass(session, wa_service)
    return flow.handle('', None, None)
