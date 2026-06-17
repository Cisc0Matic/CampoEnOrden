from .pulverizacion import PulverizacionFlow
from .fertilizacion import FertilizacionFlow
from .siembra import SiembraFlow
from .cosecha import CosechaFlow
from .combustible import CombustibleFlow
from .mantenimiento import MantenimientoFlow

FLOW_REGISTRY = {
    'pulverizacion': PulverizacionFlow,
    'fertilizacion': FertilizacionFlow,
    'siembra': SiembraFlow,
    'cosecha': CosechaFlow,
    'combustible': CombustibleFlow,
    'mantenimiento': MantenimientoFlow,
}


def get_flow_class(name: str):
    return FLOW_REGISTRY.get(name)


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
