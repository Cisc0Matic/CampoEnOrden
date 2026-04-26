from django.contrib import admin
from .models import Campo, Lote

@admin.register(Campo)
class CampoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'ubicacion', 'superficie_total')
    search_fields = ('nombre', 'ubicacion')

@admin.register(Lote)
class LoteAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'campo', 'superficie', 'cultivo_actual')
    list_filter = ('campo',)
    search_fields = ('nombre', 'cultivo_actual')