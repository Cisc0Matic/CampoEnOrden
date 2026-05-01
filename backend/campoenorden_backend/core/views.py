from rest_framework import viewsets, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db.models import Sum, Count, Q, F
from django.db.models.functions import Coalesce
from .models import (
    Campo, Persona, Campana, Lote, Cultivo, Insumo, 
    Labor, LaborInsumo, Flete, Documento, Parametro
)
from .serializers import (
    CampoSerializer, PersonaSerializer, CampanaSerializer, LoteSerializer,
    CultivoSerializer, InsumoSerializer, LaborSerializer, 
    LaborInsumoSerializer, FleteSerializer, DocumentoSerializer, 
    ParametroSerializer, DashboardSerializer
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


class CampoViewSet(viewsets.ModelViewSet):
    queryset = Campo.objects.all().prefetch_related('locadores', 'locatarios', 'documentos')
    serializer_class = CampoSerializer
    filterset_fields = ['estado_contrato']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        include_stats = self.request.query_params.get('include_stats', False)
        if include_stats:
            queryset = queryset.annotate(
                documentos_count=Count('documentos', distinct=True),
                locadores_nombres=Count('locadores'),
                locatarios_nombres=Count('locatarios')
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
    queryset = Labor.objects.all()
    serializer_class = LaborSerializer
    filterset_fields = ['lote', 'tipo', 'fecha', 'contratista']
    
    def perform_create(self, serializer):
        # Handle nested insumos
        insumos_data = self.request.data.get('insumos', [])
        instance = serializer.save()
        for insumo_data in insumos_data:
            insumo_data['labor'] = instance.id
            insumo_serializer = LaborInsumoSerializer(data=insumo_data)
            if insumo_serializer.is_valid():
                insumo_serializer.save()
        return instance
    
    def perform_update(self, serializer):
        # Handle nested insumos
        insumos_data = self.request.data.get('insumos', [])
        instance = serializer.save()
        # Delete existing insumos and recreate
        instance.insumos.all().delete()
        for insumo_data in insumos_data:
            insumo_data['labor'] = instance.id
            insumo_serializer = LaborInsumoSerializer(data=insumo_data)
            if insumo_serializer.is_valid():
                insumo_serializer.save()
        return instance


class FleteViewSet(viewsets.ModelViewSet):
    queryset = Flete.objects.all()
    serializer_class = FleteSerializer
    filterset_fields = ['estado', 'chofer', 'lote']


class DocumentoViewSet(viewsets.ModelViewSet):
    queryset = Documento.objects.all()
    serializer_class = DocumentoSerializer
    filterset_fields = ['tipo', 'estado', 'campo', 'titular', 'labor', 'flete']
    
    def perform_create(self, serializer):
        # Handle file upload
        archivo = self.request.FILES.get('archivo')
        if archivo:
            instance = serializer.save(archivo=archivo)
        else:
            instance = serializer.save()
        return instance
    
    def perform_update(self, serializer):
        # Handle file upload
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
    from django.db.models import Value
    from django.db.models.fields import DecimalField, IntegerField
    
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
def lista_campos(request):
    campos = Campo.objects.all()
    return Response(CampoSerializer(campos, many=True).data)


@api_view(['GET'])
def lista_lotes(request):
    lotes = Lote.objects.select_related('campo', 'campana', 'cultivo').all()
    return Response(LoteSerializer(lotes, many=True).data)


@api_view(['GET'])
def lista_labores(request):
    labores = Labor.objects.select_related('lote__campo', 'contratista').prefetch_related('insumos').all()
    return Response(LaborSerializer(labores, many=True).data)


@api_view(['GET'])
def lista_fletes(request):
    fletes = Flete.objects.select_related('chofer', 'lote__campo').all()
    return Response(FleteSerializer(fletes, many=True).data)


@api_view(['GET'])
def lista_documentos(request):
    documentos = Documento.objects.select_related('campo', 'titular').all()
    return Response(DocumentoSerializer(documentos, many=True).data)