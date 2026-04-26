from django.contrib import admin
from .models import (
    Campo, Persona, Campana, Lote, Cultivo, Insumo, 
    Labor, LaborInsumo, Flete, Documento, Parametro
)


@admin.register(Campo)
class CampoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'ubicacion', 'superficie_total', 'estado_contrato')
    list_filter = ('estado_contrato',)
    search_fields = ('nombre', 'ubicacion')


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


@admin.register(Labor)
class LaborAdmin(admin.ModelAdmin):
    list_display = ('tipo', 'lote', 'fecha', 'contratista', 'hectareas')
    list_filter = ('tipo', 'fecha', 'contratista')
    search_fields = ('lote__campo__nombre',)


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