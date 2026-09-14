import django_filters
from .models import Labor


class LaborFilter(django_filters.FilterSet):
    tipo__in = django_filters.CharFilter(field_name='tipo', lookup_expr='in')
    campo = django_filters.NumberFilter(field_name='lote__campo_id')

    class Meta:
        model = Labor
        fields = ['lote', 'tipo', 'estado', 'fecha', 'contratista', 'cargada_por']
