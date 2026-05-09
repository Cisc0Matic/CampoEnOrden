from django.contrib import admin
from .models import (
    Campo, Persona, Campana, Lote, Cultivo, Insumo,
    ProductoPrecio, TipoLaborPersonalizado,
    Labor, LaborInsumo, Flete, Documento, Parametro
)


@admin.register(Campo)
class CampoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'productor', 'ubicacion', 'localidad', 'provincia', 'superficie_total', 'estado_contrato')
    list_filter = ('estado_contrato', 'provincia')
    search_fields = ('nombre', 'ubicacion', 'localidad')


@admin.register(Persona)
class PersonaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'tipo', 'rol', 'documento', 'activo')
    list_filter = ('tipo', 'rol', 'activo')
    search_fields = ('nombre', 'documento', 'cuil')


@admin.register(Campana)
class CampanaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'inicio', 'fin', 'activa')
    list_filter = ('activa',)
    ordering = ('-inicio',)


@admin.register(Lote)
class LoteAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'campo', 'campana', 'cultivo', 'superficie')
    list_filter = ('campana', 'cultivo', 'activo')
    search_fields = ('nombre',)


@admin.register(Cultivo)
class CultivoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'abreviatura', 'familia', 'activo')
    list_filter = ('familia', 'activo')


@admin.register(Insumo)
class InsumoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'tipo', 'unidad', 'activo')
    list_filter = ('tipo', 'activo')


@admin.register(ProductoPrecio)
class ProductoPrecioAdmin(admin.ModelAdmin):
    list_display = ('insumo', 'precio_unitario', 'moneda', 'proveedor', 'fecha_precio')
    list_filter = ('moneda',)
    search_fields = ('insumo__nombre',)


@admin.register(TipoLaborPersonalizado)
class TipoLaborPersonalizadoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'activo')
    list_filter = ('activo',)


@admin.register(Labor)
class LaborAdmin(admin.ModelAdmin):
    list_display = ('tipo', 'lote', 'fecha', 'hectareas', 'estado', 'contratista', 'cargada_por')
    list_filter = ('tipo', 'estado', 'fecha')
    search_fields = ('lote__campo__nombre',)


@admin.register(LaborInsumo)
class LaborInsumoAdmin(admin.ModelAdmin):
    list_display = ('labor', 'insumo', 'total_aplicado', 'dosis_calculada', 'precio_unitario', 'costo_total')


@admin.register(Flete)
class FleteAdmin(admin.ModelAdmin):
    list_display = ('nro_cpe', 'chofer', 'patente_camion', 'estado')
    list_filter = ('estado',)
    search_fields = ('nro_cpe', 'patente_camion', 'chofer__nombre')


@admin.register(Documento)
class DocumentoAdmin(admin.ModelAdmin):
    list_display = ('tipo', 'numero', 'campo', 'titular', 'estado', 'monto')
    list_filter = ('tipo', 'estado')
    search_fields = ('numero',)


@admin.register(Parametro)
class ParametroAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'categoria', 'valor', 'unidad', 'campana', 'vigente')
    list_filter = ('categoria', 'vigente')
    search_fields = ('nombre',)
