import logging

from .base import BaseFlow
from .menu import get_campos_submenu

logger = logging.getLogger(__name__)


class CamposFlow(BaseFlow):
    """
    Multi-step flow for selecting a campo and viewing its lotes.
    Entered when the user selects CAMPOS_LOTES from the campos submenu.
    """
    FLOW_NAME = 'campos_lotes'

    def step_0(self, message, media_id, mime_type):
        campos = self._get_campos()
        if not campos:
            return self._finish_with_submenu(
                'No hay campos registrados en el sistema.',
                get_campos_submenu,
            )
        rows = [{'id': str(i + 1), 'title': c.nombre} for i, c in enumerate(campos)]
        self.data = {'campos_ids': [c.id for c in campos]}
        self._advance_to(1)
        return self._interactive_list(
            'Seleccioná el campo para ver sus lotes:',
            [{'title': 'Campos', 'rows': rows}],
            header='Ver lotes',
        )

    def step_1(self, message, media_id, mime_type):
        campos_ids = self.data.get('campos_ids', [])
        n = self._parse_int(message, 1, len(campos_ids))
        if n is None:
            return self._invalid(len(campos_ids))

        from core.models import Campo, Lote, Campana
        campo = Campo.objects.get(id=campos_ids[n - 1])
        campana = Campana.objects.filter(activa=True).first()

        if not campana:
            return self._finish_with_submenu(
                f'*{campo.nombre}* — No hay campaña activa configurada.',
                get_campos_submenu,
            )

        lotes = list(Lote.objects.filter(campo=campo, campana=campana).order_by('nombre'))

        if not lotes:
            return self._finish_with_submenu(
                f'*{campo.nombre}* — No hay lotes registrados en la campaña {campana.nombre}.',
                get_campos_submenu,
            )

        lines = [f'🗺️ *{campo.nombre}* — Campaña {campana.nombre}\n']
        for lote in lotes:
            cultivo = lote.cultivo.nombre if lote.cultivo else 'Sin cultivo'
            lines.append(f'• *{lote.nombre}* — {lote.superficie} ha · {cultivo}')

        sup_total = sum(float(l.superficie) for l in lotes)
        lines.append(f'\n_Total: {sup_total:.1f} ha · {len(lotes)} lotes_')

        return self._finish_with_submenu('\n'.join(lines), get_campos_submenu)


def ver_todos_los_campos(session=None) -> str:
    """Returns a formatted text with all campos and their total area."""
    from core.models import Campo, Campana, Lote
    from core.scoping import filtro_campo
    qs = Campo.objects.all()
    if session is not None and getattr(session, 'user', None):
        qs = qs.filter(filtro_campo(session.user))
    campos = list(qs.order_by('nombre'))
    if not campos:
        return None

    campana = Campana.objects.filter(activa=True).first()
    lines = ['🗺️ *Mis Campos*\n']
    for campo in campos:
        linea = f'• *{campo.nombre}*'
        if campo.superficie_total:
            linea += f' — {campo.superficie_total} ha'
        if campo.localidad:
            linea += f' ({campo.localidad})'
        if campana:
            n_lotes = Lote.objects.filter(campo=campo, campana=campana).count()
            if n_lotes:
                linea += f' · {n_lotes} lotes'
        lines.append(linea)

    if campana:
        lines.append(f'\n_Campaña activa: {campana.nombre}_')
    return '\n'.join(lines)
