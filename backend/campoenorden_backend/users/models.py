import secrets
from datetime import timedelta
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


def _expires(hours):
    return timezone.now() + timedelta(hours=hours)


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN_PRINCIPAL = "ADMIN_PRINCIPAL", "Admin Principal"
        ADMIN_EMPRESA = "ADMIN_EMPRESA", "Admin de Empresa"
        OPERARIO = "OPERARIO", "Operario"
        CONSULTA = "CONSULTA", "Usuario de Consulta"
        PRODUCTOR = "PRODUCTOR", "Cliente / Productor"

    base_role = Role.OPERARIO

    role = models.CharField(max_length=50, choices=Role.choices, default=base_role)
    dni = models.CharField(max_length=20, blank=True, null=True, unique=True)
    telefono = models.CharField(max_length=50, blank=True, null=True)
    empresa = models.ForeignKey(
        'core.Persona', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='usuarios'
    )
    persona = models.OneToOneField(
        'core.Persona', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='auth_user'
    )
    permisos_especiales = models.JSONField(default=dict, blank=True)
    fecha_alta = models.DateTimeField(blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.pk:
            if self.role is None:
                self.role = self.base_role
            if not self.fecha_alta:
                self.fecha_alta = timezone.now()
        super().save(*args, **kwargs)

    def vincular_productor(self):
        """Crea y vincula la Persona rol PRODUCTOR del usuario productor."""
        if self.role != self.Role.PRODUCTOR:
            return None
        if self.persona_id:
            return self.persona
        from core.models import Persona
        persona = Persona.objects.create(
            nombre=self.get_full_name() or self.username,
            tipo=Persona.TipoPersona.PERSONA,
            rol=Persona.Rol.PRODUCTOR,
            documento=self.dni or None,
            email=self.email or None,
            telefono=self.telefono or None,
            empresa=self.empresa,
        )
        self.persona = persona
        self.save(update_fields=['persona'])
        return persona


class EmailVerificationToken(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='verification_token')
    token = models.CharField(max_length=64, unique=True)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    def is_valid(self):
        return timezone.now() < self.expires_at

    @classmethod
    def create_for_user(cls, user):
        cls.objects.filter(user=user).delete()
        return cls.objects.create(
            user=user,
            token=secrets.token_urlsafe(32),
            expires_at=_expires(24),
        )


class Invitacion(models.Model):
    email = models.EmailField()
    role = models.CharField(max_length=50, choices=User.Role.choices)
    empresa = models.ForeignKey('core.Persona', on_delete=models.CASCADE, related_name='invitaciones')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='invitaciones_enviadas')
    token = models.CharField(max_length=64, unique=True)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    accepted_at = models.DateTimeField(null=True, blank=True)

    @property
    def is_valid(self):
        return self.accepted_at is None and timezone.now() < self.expires_at

    @classmethod
    def create(cls, email, role, empresa, created_by):
        return cls.objects.create(
            email=email,
            role=role,
            empresa=empresa,
            created_by=created_by,
            token=secrets.token_urlsafe(32),
            expires_at=_expires(48),
        )


class UserAuditLog(models.Model):
    """Bitácora de acciones administrativas del panel de administración."""

    actor = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='audit_logs_actor'
    )
    action = models.CharField(max_length=50)
    target_type = models.CharField(max_length=30, blank=True, null=True)
    target_id = models.CharField(max_length=50, blank=True, null=True)
    target_desc = models.CharField(max_length=255, blank=True, null=True)
    payload = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Bitácora de acción"
        verbose_name_plural = "Bitácoras de acciones"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.actor} -> {self.action} ({self.target_desc})"


class Pago(models.Model):
    """Pagos (manuales) que las empresas realizan a CampoEnOrden por el servicio."""

    class Concepto(models.TextChoices):
        MATRICULA = "MATRICULA", "Matrícula"
        MENSUALIDAD = "MENSUALIDAD", "Mensualidad"
        SERVICIO = "SERVICIO", "Servicio especial"
        OTRO = "OTRO", "Otro"

    class Estado(models.TextChoices):
        RECIBIDO = "RECIBIDO", "Recibido"
        PENDIENTE = "PENDIENTE", "Pendiente"
        ANULADO = "ANULADO", "Anulado"

    empresa = models.ForeignKey(
        'core.Persona', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='pagos_plataforma'
    )
    concepto = models.CharField(max_length=20, choices=Concepto.choices, default=Concepto.MENSUALIDAD)
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    moneda = models.CharField(max_length=10, default="USD")
    fecha = models.DateField()
    metodo = models.CharField(max_length=50, blank=True, null=True)
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.RECIBIDO)
    referencia = models.CharField(max_length=100, blank=True, null=True)
    observaciones = models.TextField(blank=True, null=True)
    registrado_por = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='pagos_registrados'
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Pago a CampoEnOrden"
        verbose_name_plural = "Pagos a CampoEnOrden"
        ordering = ['-fecha', '-id']

    def __str__(self):
        return f"{self.empresa} - {self.get_concepto_display()} - {self.monto} {self.moneda}"


class PasswordResetToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reset_tokens')
    token = models.CharField(max_length=64, unique=True)
    expires_at = models.DateTimeField()
    used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_valid(self):
        return not self.used and timezone.now() < self.expires_at

    @classmethod
    def create_for_user(cls, user):
        cls.objects.filter(user=user, used=False).update(used=True)
        return cls.objects.create(
            user=user,
            token=secrets.token_urlsafe(32),
            expires_at=_expires(1),
        )
