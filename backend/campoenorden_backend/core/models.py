from django.db import models

class Campo(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    ubicacion = models.CharField(max_length=255, blank=True, null=True)
    superficie_total = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    # Otros campos relevantes para un campo

    class Meta:
        verbose_name = "Campo"
        verbose_name_plural = "Campos"

    def __str__(self):
        return self.nombre

class Lote(models.Model):
    campo = models.ForeignKey(Campo, on_delete=models.CASCADE, related_name='lotes')
    nombre = models.CharField(max_length=100)
    superficie = models.DecimalField(max_digits=10, decimal_places=2)
    cultivo_actual = models.CharField(max_length=100, blank=True, null=True)
    # Otros campos relevantes para un lote

    class Meta:
        verbose_name = "Lote"
        verbose_name_plural = "Lotes"
        unique_together = ('campo', 'nombre') # Un lote con el mismo nombre no puede existir en el mismo campo

    def __str__(self):
        return f"{self.nombre} ({self.campo.nombre})"