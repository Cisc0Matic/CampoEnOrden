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
    permisos_especiales = models.JSONField(default=dict, blank=True)
    fecha_alta = models.DateTimeField(blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.pk:
            self.role = self.base_role
            if not self.fecha_alta:
                self.fecha_alta = timezone.now()
        super().save(*args, **kwargs)


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
