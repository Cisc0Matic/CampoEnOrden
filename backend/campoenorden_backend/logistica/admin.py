from django.contrib import admin
from .models import Flete

@admin.register(Flete)
class FleteAdmin(admin.ModelAdmin):
    list_display = ('nro_cpe', 'chofer', 'patente_camion', 'peso_origen', 'peso_destino', 'fecha_creacion')
    list_filter = ('chofer', 'patente_camion', 'fecha_creacion')
    search_fields = ('nro_cpe', 'chofer', 'patente_camion', 'patente_acoplado')
    date_hierarchy = 'fecha_creacion'