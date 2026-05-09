from rest_framework import viewsets, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db.models import Sum, Count, Q, F, Value
from django.db.models.functions import Coalesce
from django.db.models.fields import DecimalField
from .models import (
    Campo, Persona, Campana, Lote, Cultivo, Insumo,
    ProductoPrecio, TipoLaborPersonalizado,
    Labor, LaborInsumo, Flete, Documento, Parametro
)
from .serializers import (
    CampoSerializer, PersonaSerializer, CampanaSerializer, LoteSerializer,
    CultivoSerializer, InsumoSerializer, ProductoPrecioSerializer,
    TipoLaborPersonalizadoSerializer,
    LaborSerializer, LaborInsumoSerializer, FleteSerializer, DocumentoSerializer,
    ParametroSerializer, DashboardSerializer, MargenSerializer
)


class PersonaViewSet(viewsets.ModelViewSet):
    queryset = Persona.objects.all()
    serializer_class = PersonaSerializer
    search_fields = ['nombre', 'documento', 'cuil']
    filterset_fields = ['tipo', 'rol', 'activo']


class CampanaViewSet(viewsets.ModelViewSet):
    queryset = Campana.objects.all()
    serializer_class = CampanaSerializer


class CultivoViewSet(viewsets.ModelViewSet):
    queryset = Cultivo.objects.all()
    serializer_class = CultivoSerializer
    filterset_fields = ['familia', 'activo']


class InsumoViewSet(viewsets.ModelViewSet):
    queryset = Insumo.objects.all()
    serializer_class = InsumoSerializer
    filterset_fields = ['tipo', 'activo']


class ProductoPrecioViewSet(viewsets.ModelViewSet):
    queryset = ProductoPrecio.objects.select_related('insumo', 'proveedor').all()
    serializer_class = ProductoPrecioSerializer
    filterset_fields = ['insumo', 'moneda', 'proveedor']


class TipoLaborPersonalizadoViewSet(viewsets.ModelViewSet):
    queryset = TipoLaborPersonalizado.objects.all()
    serializer_class = TipoLaborPersonalizadoSerializer
    filterset_fields = ['activo']


class CampoViewSet(viewsets.ModelViewSet):
    queryset = Campo.objects.prefetch_related('locadores', 'locatarios', 'documentos').all()
    serializer_class = CampoSerializer
    filterset_fields = ['estado_contrato']

    def get_queryset(self):
        queryset = super().get_queryset()
        include_stats = self.request.query_params.get('include_stats', False)
        if include_stats:
            queryset = queryset.annotate(
                documentos_count=Count('documentos', distinct=True),
            )
        return queryset

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        if request.query_params.get('include_stats'):
            for campo in response.data:
                campo_obj = self.queryset.get(pk=campo['id'])
                campo['margen'] = float(campo_obj.margen or 0)
                campo['documentos_count'] = campo_obj.documentos.count()
                campo['locadores_nombres'] = ', '.join(campo_obj.locadores.values_list('nombre', flat=True)[:3])
                campo['locatarios_nombres'] = ', '.join(campo_obj.locatarios.values_list('nombre', flat=True)[:3])
        return response


class LoteViewSet(viewsets.ModelViewSet):
    queryset = Lote.objects.all()
    serializer_class = LoteSerializer
    filterset_fields = ['campo', 'campana', 'cultivo', 'activo']


class LaborViewSet(viewsets.ModelViewSet):
    queryset = Labor.objects.select_related(
        'lote__campo', 'contratista', 'responsable',
        'cargada_por', 'revisada_por', 'sub_tipo_otra'
    ).prefetch_related('insumos__insumo').all()
    serializer_class = LaborSerializer
    filterset_fields = ['lote', 'tipo', 'estado', 'fecha', 'contratista', 'cargada_por']

    def perform_create(self, serializer):
        insumos_data = self.request.data.get('insumos', [])
        serializer.save()

    def perform_update(self, serializer):
        serializer.save()


class FleteViewSet(viewsets.ModelViewSet):
    queryset = Flete.objects.all()
    serializer_class = FleteSerializer
    filterset_fields = ['estado', 'chofer', 'lote']


class DocumentoViewSet(viewsets.ModelViewSet):
    queryset = Documento.objects.all()
    serializer_class = DocumentoSerializer
    filterset_fields = ['tipo', 'estado', 'campo', 'titular', 'labor', 'flete']

    def perform_create(self, serializer):
        archivo = self.request.FILES.get('archivo')
        if archivo:
            instance = serializer.save(archivo=archivo)
        else:
            instance = serializer.save()
        return instance

    def perform_update(self, serializer):
        archivo = self.request.FILES.get('archivo')
        if archivo:
            instance = serializer.save(archivo=archivo)
        else:
            instance = serializer.save()
        return instance


class ParametroViewSet(viewsets.ModelViewSet):
    queryset = Parametro.objects.all()
    serializer_class = ParametroSerializer
    filterset_fields = ['categoria', 'campana', 'vigente']


@api_view(['GET'])
def dashboard(request):
    campos_activos = Campo.objects.filter(estado_contrato='ACTIVO').count()
    hectareas_totales = Campo.objects.aggregate(
        total=Coalesce(Sum('superficie_total'), Value(0, output_field=DecimalField()))
    )['total']
    hectareas_trabajadas = Campo.objects.aggregate(
        total=Coalesce(Sum('superficie_trabajada'), Value(0, output_field=DecimalField()))
    )['total']
    labors_count = Labor.objects.count()

    costos_labores = Labor.objects.aggregate(
        total=Coalesce(Sum('costo_total'), Value(0, output_field=DecimalField()))
    )['total']
    costos_fletes_corto = Flete.objects.aggregate(
        total=Coalesce(Sum('flete_corto'), Value(0, output_field=DecimalField()))
    )['total']
    costos_fletes_largo = Flete.objects.aggregate(
        total=Coalesce(Sum('flete_largo'), Value(0, output_field=DecimalField()))
    )['total']
    costos_fletes = costos_fletes_corto + costos_fletes_largo
    costos_totales = costos_labores + costos_fletes

    if hectareas_trabajadas and hectareas_trabajadas > 0:
        costos_por_ha = costos_totales / hectareas_trabajadas
    else:
        costos_por_ha = 0

    documentos_pendientes = Documento.objects.filter(estado='PENDIENTE').count()

    alertas = []
    campos_vencidos = Campo.objects.filter(estado_contrato='VENCIDO')
    if campos_vencidos.exists():
        alertas.append(f"{campos_vencidos.count()} campo(s) con contrato vencido(s)")

    docs_vencidos = Documento.objects.filter(estado='VENCIDO')
    if docs_vencidos.exists():
        alertas.append(f"{docs_vencidos.count()} documento(s) vencido(s)")

    data = {
        'campos_activos': campos_activos,
        'hectareas_totales': hectareas_totales,
        'hectareas_trabajadas': hectareas_trabajadas,
        'labores_cargadas': labors_count,
        'costos_totales': costos_totales,
        'costos_por_ha': costos_por_ha,
        'documentos_pendientes': documentos_pendientes,
        'alertas': alertas
    }
    return Response(data)


@api_view(['GET'])
def indicadores_campo(request, campo_id):
    try:
        campo = Campo.objects.get(pk=campo_id)
    except Campo.DoesNotExist:
        return Response({'error': 'Campo no encontrado'}, status=status.HTTP_404_NOT_FOUND)

    costos_labores = Labor.objects.filter(lote__campo=campo).aggregate(
        total=Coalesce(Sum('costo_total'), 0)
    )['total']

    data = {
        'campo': CampoSerializer(campo).data,
        'costo_total': costos_labores,
        'costo_por_ha': float(campo.costo_por_ha or 0),
        'margen': float(campo.margen or 0),
        'alquiler_pendiente': float(campo.alquiler_pendiente or 0),
        'documentos_asociados': campo.documentos.count()
    }
    return Response(data)


@api_view(['GET'])
def margen_view(request):
    campo_id = request.query_params.get('campo')
    lote_id = request.query_params.get('lote')
    campana_id = request.query_params.get('campana')

    labores_qs = Labor.objects.all()
    if campo_id:
        labores_qs = labores_qs.filter(lote__campo_id=campo_id)
    if lote_id:
        labores_qs = labores_qs.filter(lote_id=lote_id)
    if campana_id:
        labores_qs = labores_qs.filter(lote__campana_id=campana_id)

    costos_insumos = LaborInsumo.objects.filter(
        labor__in=labores_qs
    ).aggregate(
        total=Coalesce(Sum('costo_total'), Value(0, output_field=DecimalField()))
    )['total']

    costos_labores = labores_qs.aggregate(
        total=Coalesce(Sum('costo_total'), Value(0, output_field=DecimalField()))
    )['total']

    hectareas_totales = labores_qs.aggregate(
        total=Coalesce(Sum('hectareas'), Value(0, output_field=DecimalField()))
    )['total']

    ingresos = 0
    lotes_qs = Lote.objects.all()
    if campo_id:
        lotes_qs = lotes_qs.filter(campo_id=campo_id)
    if lote_id:
        lotes_qs = lotes_qs.filter(id=lote_id)
    if campana_id:
        lotes_qs = lotes_qs.filter(campana_id=campana_id)

    for l in lotes_qs:
        if l.rendimiento_estimado and l.precio_tn:
            ingresos += float(l.rendimiento_estimado) * float(l.precio_tn)

    ha = float(hectareas_totales) if hectareas_totales else 1
    costo_total = float(costos_insumos) + float(costos_labores)
    margen_bruto = ingresos - costo_total
    roi = ((margen_bruto / costo_total) * 100) if costo_total else 0

    def calc_pct(c):
        return round((c / costo_total) * 100, 2) if costo_total else 0

    data = {
        'conceptos': [
            {
                'concepto': 'Insumos',
                'usd_total': round(float(costos_insumos), 2),
                'usd_ha': round(float(costos_insumos) / ha, 2),
                'porc_costo_total': calc_pct(float(costos_insumos)),
            },
            {
                'concepto': 'Labores',
                'usd_total': round(float(costos_labores), 2),
                'usd_ha': round(float(costos_labores) / ha, 2),
                'porc_costo_total': calc_pct(float(costos_labores)),
            },
            {
                'concepto': 'Cosecha',
                'usd_total': 0,
                'usd_ha': 0,
                'porc_costo_total': 0,
            },
            {
                'concepto': 'Comercialización',
                'usd_total': 0,
                'usd_ha': 0,
                'porc_costo_total': 0,
            },
        ],
        'total_costos_variables': round(costo_total, 2),
        'ingreso_bruto': round(ingresos, 2),
        'margen_bruto': round(margen_bruto, 2),
        'costo_directo_alquiler': 0,
        'margen_bruto_directo': round(margen_bruto, 2),
        'rentabilidad_roi': round(roi, 2),
        'hectareas': round(ha, 2),
    }
    return Response(data)


@api_view(['GET'])
def lista_campos(request):
    campos = Campo.objects.all()
    return Response(CampoSerializer(campos, many=True).data)


@api_view(['GET'])
def lista_lotes(request):
    lotes = Lote.objects.select_related('campo', 'campana', 'cultivo').all()
    return Response(LoteSerializer(lotes, many=True).data)


@api_view(['GET'])
def lista_labores(request):
    labores = Labor.objects.select_related(
        'lote__campo', 'contratista', 'responsable',
        'cargada_por', 'revisada_por', 'sub_tipo_otra'
    ).prefetch_related('insumos__insumo').all()
    return Response(LaborSerializer(labores, many=True).data)


@api_view(['GET'])
def lista_fletes(request):
    fletes = Flete.objects.select_related('chofer', 'lote__campo').all()
    return Response(FleteSerializer(fletes, many=True).data)


@api_view(['GET'])
def lista_documentos(request):
    documentos = Documento.objects.select_related('campo', 'titular').all()
    return Response(DocumentoSerializer(documentos, many=True).data)
