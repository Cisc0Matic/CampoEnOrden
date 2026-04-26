from django.db import models

class Flete(models.Model):
    nro_cpe = models.CharField(max_length=50, unique=True, verbose_name="Número de CPE")
    ctg = models.CharField(max_length=50, blank=True, null=True, verbose_name="Código de Trazabilidad Geográfica")
    patente_camion = models.CharField(max_length=10, verbose_name="Patente Camión")
    patente_acoplado = models.CharField(max_length=10, blank=True, null=True, verbose_name="Patente Acoplado")
    chofer = models.CharField(max_length=100)
    peso_origen = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    peso_destino = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    ultima_modificacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Flete"
        verbose_name_plural = "Fletes"
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f"Flete {self.nro_cpe} - {self.chofer}"