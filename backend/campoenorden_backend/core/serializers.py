from rest_framework import serializers
from .models import (
    Campo, Persona, Campana, Lote, Cultivo, Insumo,
    ProductoPrecio, TipoLaborPersonalizado,
    Labor, LaborInsumo, Flete, Documento, Parametro
)


class PersonaSerializer(serializers.ModelSerializer):
    nombre_rol = serializers.CharField(source='get_rol_display', read_only=True)

    class Meta:
        model = Persona
        fields = '__all__'


class CampanaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Campana
        fields = '__all__'


class CultivoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cultivo
        fields = '__all__'


class InsumoSerializer(serializers.ModelSerializer):
    nombre_tipo = serializers.CharField(source='get_tipo_display', read_only=True)

    class Meta:
        model = Insumo
        fields = '__all__'


class ProductoPrecioSerializer(serializers.ModelSerializer):
    insumo_nombre = serializers.CharField(source='insumo.nombre', read_only=True)
    proveedor_nombre = serializers.CharField(source='proveedor.nombre', read_only=True)

    class Meta:
        model = ProductoPrecio
        fields = '__all__'


class TipoLaborPersonalizadoSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoLaborPersonalizado
        fields = '__all__'


class CampoSerializer(serializers.ModelSerializer):
    estado_contrato_display = serializers.CharField(source='get_estado_contrato_display', read_only=True)
    costo_total_display = serializers.SerializerMethodField()
    locadores_nombres = serializers.SerializerMethodField()
    locatarios_nombres = serializers.SerializerMethodField()
    documentos_count = serializers.IntegerField(read_only=True, default=0)
    productor_nombre = serializers.CharField(source='productor.nombre', read_only=True, default=None)
    locadores = serializers.PrimaryKeyRelatedField(many=True, read_only=False, queryset=Persona.objects.all(), required=False)
    locatarios = serializers.PrimaryKeyRelatedField(many=True, read_only=False, queryset=Persona.objects.all(), required=False)
    productor = serializers.PrimaryKeyRelatedField(queryset=Persona.objects.all(), required=False, allow_null=True)

    class Meta:
        model = Campo
        fields = '__all__'

    def get_costo_total_display(self, obj):
        return float(obj.costo_total or 0)

    def get_locadores_nombres(self, obj):
        return ', '.join(obj.locadores.values_list('nombre', flat=True)[:3])

    def get_locatarios_nombres(self, obj):
        return ', '.join(obj.locatarios.values_list('nombre', flat=True)[:3])


class LoteSerializer(serializers.ModelSerializer):
    cultivo_nombre = serializers.CharField(source='cultivo.nombre', read_only=True)
    campo_nombre = serializers.CharField(source='campo.nombre', read_only=True)
    campana_nombre = serializers.CharField(source='campana.nombre', read_only=True)
    campo = serializers.PrimaryKeyRelatedField(queryset=Campo.objects.all())
    campana = serializers.PrimaryKeyRelatedField(queryset=Campana.objects.all())
    cultivo = serializers.PrimaryKeyRelatedField(queryset=Cultivo.objects.all())

    class Meta:
        model = Lote
        fields = '__all__'


class LaborInsumoSerializer(serializers.ModelSerializer):
    insumo_nombre = serializers.CharField(source='insumo.nombre', read_only=True)
    insumo = serializers.PrimaryKeyRelatedField(queryset=Insumo.objects.all())

    class Meta:
        model = LaborInsumo
        fields = '__all__'
        read_only_fields = ['dosis_calculada', 'costo_total']


class LaborSerializer(serializers.ModelSerializer):
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    lote_nombre = serializers.CharField(source='lote.campo.nombre', read_only=True)
    contratista_nombre = serializers.CharField(source='contratista.nombre', read_only=True, default=None)
    responsable_nombre = serializers.CharField(source='responsable.nombre', read_only=True, default=None)
    cargada_por_nombre = serializers.CharField(source='cargada_por.username', read_only=True, default=None)
    revisada_por_nombre = serializers.CharField(source='revisada_por.username', read_only=True, default=None)
    sub_tipo_otra_nombre = serializers.CharField(source='sub_tipo_otra.nombre', read_only=True, default=None)
    insumos = LaborInsumoSerializer(many=True, read_only=True)
    lote = serializers.PrimaryKeyRelatedField(queryset=Lote.objects.all())
    contratista = serializers.PrimaryKeyRelatedField(queryset=Persona.objects.all(), required=False, allow_null=True)
    responsable = serializers.PrimaryKeyRelatedField(queryset=Persona.objects.all(), required=False, allow_null=True)
    sub_tipo_otra = serializers.PrimaryKeyRelatedField(queryset=TipoLaborPersonalizado.objects.all(), required=False, allow_null=True)
    foto_receta_url = serializers.SerializerMethodField()

    class Meta:
        model = Labor
        fields = '__all__'
        read_only_fields = ['cargada_por', 'fecha_hora_carga', 'revisada_por', 'fecha_revision', 'costo_total']

    def get_foto_receta_url(self, obj):
        if obj.foto_receta:
            return obj.foto_receta.url
        return None

    def create(self, validated_data):
        request = self.context.get('request')
        insumos_data = self.context.get('insumos', [])
        if request and hasattr(request, 'user'):
            validated_data['cargada_por'] = request.user
        labor = Labor.objects.create(**validated_data)
        for insumo_data in insumos_data:
            LaborInsumo.objects.create(labor=labor, **insumo_data)
        return labor

    def update(self, instance, validated_data):
        insumos_data = self.context.get('insumos', [])
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if instance.estado == Labor.EstadoLabor.REVISADA and not instance.revisada_por:
            request = self.context.get('request')
            if request and hasattr(request, 'user'):
                import datetime
                instance.revisada_por = request.user
                instance.fecha_revision = datetime.datetime.now()
        instance.save()

        if insumos_data:
            instance.insumos.all().delete()
            for insumo_data in insumos_data:
                LaborInsumo.objects.create(labor=instance, **insumo_data)
        return instance


class FleteSerializer(serializers.ModelSerializer):
    chofer_nombre = serializers.CharField(source='chofer.nombre', read_only=True)
    lote_info = serializers.CharField(source='lote.__str__', read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    costo_total_flete = serializers.SerializerMethodField()

    class Meta:
        model = Flete
        fields = '__all__'

    def get_costo_total_flete(self, obj):
        total = (obj.flete_corto or 0) + (obj.flete_largo or 0) + (obj.comision or 0) + (obj.secada or 0) + (obj.cosecha or 0) + (obj.costo_comercial or 0)
        return float(total)


class DocumentoSerializer(serializers.ModelSerializer):
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    campo_nombre = serializers.CharField(source='campo.nombre', read_only=True)
    titular_nombre = serializers.CharField(source='titular.nombre', read_only=True)
    lote_info = serializers.CharField(source='lote.__str__', read_only=True)

    class Meta:
        model = Documento
        fields = '__all__'
        extra_kwargs = {
            'archivo': {'required': False, 'allow_null': True}
        }

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if instance.archivo:
            data['archivo_url'] = instance.archivo.url
        return data


class ParametroSerializer(serializers.ModelSerializer):
    categoria_display = serializers.CharField(source='get_categoria_display', read_only=True)
    campana_nombre = serializers.CharField(source='campana.nombre', read_only=True)

    class Meta:
        model = Parametro
        fields = '__all__'


class DashboardSerializer(serializers.Serializer):
    campos_activos = serializers.IntegerField()
    hectareas_totales = serializers.DecimalField(max_digits=10, decimal_places=2)
    hectareas_trabajadas = serializers.DecimalField(max_digits=10, decimal_places=2)
    labores_cargadas = serializers.IntegerField()
    costos_totales = serializers.DecimalField(max_digits=14, decimal_places=2)
    costos_por_ha = serializers.DecimalField(max_digits=10, decimal_places=2)
    documentos_pendientes = serializers.IntegerField()
    alertas = serializers.ListField()


class MargenSerializer(serializers.Serializer):
    concepto = serializers.CharField()
    usd_total = serializers.DecimalField(max_digits=14, decimal_places=2)
    usd_ha = serializers.DecimalField(max_digits=10, decimal_places=2)
    moneda_local_ha = serializers.DecimalField(max_digits=10, decimal_places=2)
    qq_ha = serializers.DecimalField(max_digits=10, decimal_places=2)
    porc_costo_total = serializers.DecimalField(max_digits=6, decimal_places=2)
