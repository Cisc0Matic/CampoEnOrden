from django.db import models
from core.models import Lote # Import Lote from the core app

class Labor(models.Model):
    lote = models.ForeignKey(Lote, on_delete=models.CASCADE, related_name='labores')
    fecha = models.DateField()
    tipo_aplicacion = models.CharField(max_length=100)
    insumos = models.TextField(blank=True, null=True) # e.g., "Fertilizante A, 100kg; Herbicida B, 5L"
    costo = models.DecimalField(max_digits=10, decimal_places=2)
    observaciones = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Labor"
        verbose_name_plural = "Labores"
        ordering = ['-fecha'] # Ordenar por fecha descendente

    def __str__(self):
        return f"Labor de {self.tipo_aplicacion} en {self.lote.nombre} ({self.fecha})"