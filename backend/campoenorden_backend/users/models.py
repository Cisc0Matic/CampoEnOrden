from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN_PRINCIPAL = "ADMIN_PRINCIPAL", "Admin Principal"
        ADMIN_EMPRESA = "ADMIN_EMPRESA", "Admin de Empresa"
        OPERARIO = "OPERARIO", "Operario"
        CONSULTA = "CONSULTA", "Usuario de Consulta"
        PRODUCTOR = "PRODUCTOR", "Cliente / Productor"

    base_role = Role.OPERARIO

    role = models.CharField(max_length=50, choices=Role.choices, default=base_role)
    telefono = models.CharField(max_length=50, blank=True, null=True)
    empresa = models.ForeignKey(
        'core.Persona', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='usuarios'
    )
    permisos_especiales = models.JSONField(default=dict, blank=True)
    fecha_alta = models.DateTimeField(blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.pk:
            self.role = self.base_role
            if not self.fecha_alta:
                from django.utils import timezone
                self.fecha_alta = timezone.now()
        super().save(*args, **kwargs)
