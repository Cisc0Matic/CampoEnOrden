from django.contrib import admin
from .models import Labor

@admin.register(Labor)
class LaborAdmin(admin.ModelAdmin):
    list_display = ('lote', 'fecha', 'tipo_aplicacion', 'costo')
    list_filter = ('lote', 'tipo_aplicacion', 'fecha')
    search_fields = ('lote__nombre', 'tipo_aplicacion', 'insumos')
    date_hierarchy = 'fecha'