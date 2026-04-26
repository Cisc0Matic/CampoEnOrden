from django.db import models

from core.models import Lote


class Labor(models.Model):
    lote = models.ForeignKey(Lote, on_delete=models.CASCADE, related_name='labores_legacy')
    fecha = models.DateField()
    tipo_aplicacion = models.CharField(max_length=100)
    insumos = models.TextField(blank=True, null=True)
    costo = models.DecimalField(max_digits=10, decimal_places=2)
    observaciones = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Labor (legacy)"
        verbose_name_plural = "Labores (legacy)"
        ordering = ['-fecha']
        related_name = 'labores_legacy'

    def __str__(self):
        return f"Labor de {self.tipo_aplicacion} en {self.lote.nombre} ({self.fecha})"