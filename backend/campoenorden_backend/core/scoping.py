from django.db.models import Q

from users.models import User


def _sin_acceso():
    return Q(pk__in=[])


def _productor_empresa(prefijo, empresa_id):
    """Campos del tenant `empresa_id`, por el vínculo del productor a la empresa
    o por la convención histórica de usar la propia persona-empresa como productor."""
    p = f'{prefijo}__' if prefijo else ''
    return (
        Q(**{f'{p}productor__empresa_id': empresa_id})
        | Q(**{f'{p}productor_id': empresa_id})
    )


def filtro_campo(user, empresa_id=None):
    """Condición para filtrar consultas directas sobre `Campo`.

    El ADMIN_PRINCIPAL puede acotar a una empresa concreta pasando `empresa_id`;
    el resto de roles siempre se escopea por su propia empresa/productor.
    """
    if user.role == User.Role.ADMIN_PRINCIPAL:
        if empresa_id:
            return _productor_empresa('', empresa_id)
        return Q()
    if user.role == User.Role.PRODUCTOR:
        if user.persona_id:
            return Q(productor_id=user.persona_id)
        return _sin_acceso()
    if user.empresa_id:
        return _productor_empresa('', user.empresa_id)
    return _sin_acceso()


def filtro_lote(user, empresa_id=None):
    """Condición para filtrar `Lote` (referencia directa a `Campo`)."""
    if user.role == User.Role.ADMIN_PRINCIPAL:
        if empresa_id:
            return _productor_empresa('campo', empresa_id)
        return Q()
    if user.role == User.Role.PRODUCTOR:
        if user.persona_id:
            return Q(campo__productor_id=user.persona_id)
        return _sin_acceso()
    if user.empresa_id:
        return _productor_empresa('campo', user.empresa_id)
    return _sin_acceso()


def filtro_via_campo(user, prefijo='lote__campo', empresa_id=None):
    """Condición para modelos que alcanzan `Campo` a través de una relación.

    `prefijo` es la ruta desde el modelo hasta `campo` (p. ej. `lote__campo`
    para `Labor`, `campo` para `Documento`, `lote__campo` para `Flete`).
    """
    if user.role == User.Role.ADMIN_PRINCIPAL:
        if empresa_id:
            return _productor_empresa(prefijo, empresa_id)
        return Q()
    if user.role == User.Role.PRODUCTOR:
        if user.persona_id:
            return Q(**{f'{prefijo}__productor_id': user.persona_id})
        return _sin_acceso()
    if user.empresa_id:
        return _productor_empresa(prefijo, user.empresa_id)
    return _sin_acceso()


def filtro_documento(user, empresa_id=None):
    """Documentos visibles: los que tocan campos visibles (vía campo, labor o flete)."""
    if user.role == User.Role.ADMIN_PRINCIPAL:
        if empresa_id:
            q_campo = filtro_via_campo(user, prefijo='campo', empresa_id=empresa_id)
            q_labor = filtro_via_campo(user, prefijo='labor__lote__campo', empresa_id=empresa_id)
            q_flete = filtro_via_campo(user, prefijo='flete__lote__campo', empresa_id=empresa_id)
            return q_campo | q_labor | q_flete
        return Q()
    q_campo = filtro_via_campo(user, prefijo='campo')
    q_labor = filtro_via_campo(user, prefijo='labor__lote__campo')
    q_flete = filtro_via_campo(user, prefijo='flete__lote__campo')
    return q_campo | q_labor | q_flete


def _personas_de_empresa(e):
    """Personas que pertenecen a la empresa `e` o intervienen en sus datos."""
    return Q(id=e) | Q(empresa_id=e) | Q(campos_productor__productor__empresa_id=e) | \
        Q(campos_productor__productor_id=e) | Q(campos_arrendatario__productor__empresa_id=e) | \
        Q(campos_dueño__productor__empresa_id=e) | \
        Q(labores_realizadas__lote__campo__productor__empresa_id=e) | \
        Q(labores_responsable__lote__campo__productor__empresa_id=e)


def filtro_persona(user, empresa_id=None):
    """Personas visibles: las de la propia empresa y las que intervienen en sus datos."""
    if user.role == User.Role.ADMIN_PRINCIPAL:
        if empresa_id:
            return _personas_de_empresa(empresa_id)
        return Q()
    if user.role == User.Role.PRODUCTOR:
        if not user.persona_id:
            return _sin_acceso()
        p = user.persona_id
        return Q(campos_productor_id=p) | Q(campos_arrendatario__productor_id=p) | \
            Q(campos_dueño__productor_id=p) | Q(labores_realizadas__lote__campo__productor_id=p) | \
            Q(labores_responsable__lote__campo__productor_id=p) | Q(fletes_chofer__lote__campo__productor_id=p)
    if user.empresa_id:
        return _personas_de_empresa(user.empresa_id)
    return _sin_acceso()


def puede_ver_campo(user, campo):
    """Chequeo a nivel objeto de acceso a un `Campo`."""
    if user.role == User.Role.ADMIN_PRINCIPAL:
        return True
    if user.role == User.Role.PRODUCTOR:
        return bool(user.persona_id and campo.productor_id == user.persona_id)
    if user.empresa_id:
        return bool(
            (campo.productor_id and campo.productor.empresa_id == user.empresa_id)
            or campo.productor_id == user.empresa_id
        )
    return False