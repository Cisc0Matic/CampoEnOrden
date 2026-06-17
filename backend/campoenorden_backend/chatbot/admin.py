from django.contrib import admin
from .models import Maquinaria, WhatsAppSession, WhatsAppMessage, RegistroCombustible, RegistroMantenimiento


@admin.register(Maquinaria)
class MaquinariaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'tipo', 'marca', 'modelo', 'ano', 'propietario', 'activo')
    list_filter = ('tipo', 'propietario', 'activo')
    search_fields = ('nombre', 'marca', 'modelo', 'dominio')


@admin.register(WhatsAppSession)
class WhatsAppSessionAdmin(admin.ModelAdmin):
    list_display = ('phone_number', 'user', 'current_flow', 'current_step', 'last_activity')
    list_filter = ('current_flow',)
    search_fields = ('phone_number', 'user__username')
    readonly_fields = ('last_activity', 'created_at')


@admin.register(WhatsAppMessage)
class WhatsAppMessageAdmin(admin.ModelAdmin):
    list_display = ('session', 'direction', 'message_type', 'content_preview', 'timestamp')
    list_filter = ('direction', 'message_type')
    readonly_fields = ('timestamp',)

    def content_preview(self, obj):
        return obj.content[:80] if obj.content else '-'
    content_preview.short_description = 'Contenido'


@admin.register(RegistroCombustible)
class RegistroCombustibleAdmin(admin.ModelAdmin):
    list_display = ('fecha', 'maquinaria', 'campo', 'proveedor', 'litros', 'total', 'cargado_por')
    list_filter = ('maquinaria', 'campo')
    search_fields = ('proveedor', 'nro_documento')


@admin.register(RegistroMantenimiento)
class RegistroMantenimientoAdmin(admin.ModelAdmin):
    list_display = ('fecha', 'maquinaria', 'tipo', 'quien_realizo', 'total', 'pago_realizado', 'cargado_por')
    list_filter = ('tipo', 'quien_realizo', 'pago_realizado')
    search_fields = ('descripcion', 'repuesto', 'taller', 'nro_factura')
