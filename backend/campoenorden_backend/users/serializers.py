from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from core.models import Persona
from .models import Invitacion, EmailVerificationToken, PasswordResetToken, User


class UserSerializer(serializers.ModelSerializer):
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    empresa_nombre = serializers.CharField(source='empresa.nombre', read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'role', 'role_display', 'dni', 'telefono',
            'empresa', 'empresa_nombre', 'permisos_especiales',
            'fecha_alta', 'is_active',
        ]
        read_only_fields = ['id', 'fecha_alta']


class RegisterSerializer(serializers.Serializer):
    empresa_nombre = serializers.CharField(max_length=255)
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True, default='')
    dni = serializers.CharField(max_length=20, required=False, allow_blank=True, default='')
    password = serializers.CharField(write_only=True)
    password_confirm = serializers.CharField(write_only=True)

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("El nombre de usuario ya está en uso.")
        return value

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Ya existe una cuenta con ese email.")
        return value

    def validate_dni(self, value):
        if value and User.objects.filter(dni=value).exclude(pk=getattr(self, 'instance', None)).exists():
            raise serializers.ValidationError("Ya existe un usuario con ese DNI.")
        return value

    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError({"password_confirm": "Las contraseñas no coinciden."})
        validate_password(data['password'])
        return data

    @transaction.atomic
    def create(self, validated_data):
        empresa = Persona.objects.create(
            nombre=validated_data['empresa_nombre'],
            tipo=Persona.TipoPersona.EMPRESA,
        )
        return User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            dni=validated_data.get('dni', '') or None,
            password=validated_data['password'],
            role=User.Role.ADMIN_EMPRESA,
            empresa=empresa,
            is_active=False,
        )


class ActivateAccountSerializer(serializers.Serializer):
    token = serializers.CharField()

    def validate_token(self, value):
        try:
            obj = EmailVerificationToken.objects.select_related('user').get(token=value)
        except EmailVerificationToken.DoesNotExist:
            raise serializers.ValidationError("Token inválido.")
        if not obj.is_valid():
            raise serializers.ValidationError("El enlace expiró. Solicitá uno nuevo.")
        self._token_obj = obj
        return value

    def save(self):
        user = self._token_obj.user
        user.is_active = True
        user.save(update_fields=['is_active'])
        self._token_obj.delete()
        return user


class ResendActivationSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        try:
            self.user = User.objects.get(email=value, is_active=False)
        except User.DoesNotExist:
            raise serializers.ValidationError("No se encontró una cuenta pendiente con ese email.")
        return value


class UpdateProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'dni', 'telefono']

    def validate_email(self, value):
        if User.objects.exclude(pk=self.instance.pk).filter(email=value).exists():
            raise serializers.ValidationError("Ya existe una cuenta con ese email.")
        return value


class InviteUserSerializer(serializers.Serializer):
    INVITABLE_ROLES = [User.Role.OPERARIO, User.Role.CONSULTA, User.Role.PRODUCTOR]

    email = serializers.EmailField()
    role = serializers.ChoiceField(choices=INVITABLE_ROLES)
    dni = serializers.CharField(max_length=20, required=False, allow_blank=True, default='')

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Ya existe un usuario con ese email.")
        pending = Invitacion.objects.filter(
            email=value, accepted_at__isnull=True, expires_at__gt=timezone.now()
        )
        if pending.exists():
            raise serializers.ValidationError("Ya hay una invitación pendiente para ese email.")
        return value

    def validate_dni(self, value):
        if value and User.objects.filter(dni=value).exists():
            raise serializers.ValidationError("Ya existe un usuario con ese DNI.")
        return value


class AdminCreateUserSerializer(serializers.Serializer):
    CREATABLE_ROLES = [User.Role.OPERARIO, User.Role.CONSULTA, User.Role.PRODUCTOR]

    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True, default='')
    dni = serializers.CharField(max_length=20, required=False, allow_blank=True, default='')
    password = serializers.CharField(write_only=True)
    role = serializers.ChoiceField(choices=CREATABLE_ROLES)

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("El nombre de usuario ya está en uso.")
        return value

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Ya existe un usuario con ese email.")
        return value

    def validate_dni(self, value):
        if value and User.objects.filter(dni=value).exists():
            raise serializers.ValidationError("Ya existe un usuario con ese DNI.")
        return value

    def validate_password(self, value):
        validate_password(value)
        return value


class AcceptInvitationSerializer(serializers.Serializer):
    token = serializers.CharField()
    username = serializers.CharField(max_length=150)
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True, default='')
    dni = serializers.CharField(max_length=20, required=False, allow_blank=True, default='')
    password = serializers.CharField(write_only=True)
    password_confirm = serializers.CharField(write_only=True)

    def validate_token(self, value):
        try:
            inv = Invitacion.objects.select_related('empresa').get(token=value)
        except Invitacion.DoesNotExist:
            raise serializers.ValidationError("Token inválido.")
        if not inv.is_valid:
            raise serializers.ValidationError("La invitación ya fue usada o expiró.")
        self._invitation = inv
        return value

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("El nombre de usuario ya está en uso.")
        return value

    def validate_dni(self, value):
        if value and User.objects.filter(dni=value).exists():
            raise serializers.ValidationError("Ya existe un usuario con ese DNI.")
        return value

    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError({"password_confirm": "Las contraseñas no coinciden."})
        validate_password(data['password'])
        return data

    def save(self):
        inv = self._invitation
        user = User.objects.create_user(
            username=self.validated_data['username'],
            email=inv.email,
            first_name=self.validated_data['first_name'],
            last_name=self.validated_data['last_name'],
            dni=self.validated_data.get('dni', '') or None,
            password=self.validated_data['password'],
            role=inv.role,
            empresa=inv.empresa,
            is_active=True,
        )
        inv.accepted_at = timezone.now()
        inv.save(update_fields=['accepted_at'])
        return user


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        try:
            self.user = User.objects.get(email=value, is_active=True)
        except User.DoesNotExist:
            self.user = None  # Don't reveal if email exists
        return value


class PasswordResetConfirmSerializer(serializers.Serializer):
    token = serializers.CharField()
    password = serializers.CharField(write_only=True)
    password_confirm = serializers.CharField(write_only=True)

    def validate_token(self, value):
        try:
            obj = PasswordResetToken.objects.select_related('user').get(token=value)
        except PasswordResetToken.DoesNotExist:
            raise serializers.ValidationError("Token inválido.")
        if not obj.is_valid():
            raise serializers.ValidationError("El enlace expiró o ya fue utilizado.")
        self._reset_token = obj
        return value

    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError({"password_confirm": "Las contraseñas no coinciden."})
        validate_password(data['password'])
        return data

    def save(self):
        user = self._reset_token.user
        user.set_password(self.validated_data['password'])
        user.save(update_fields=['password'])
        self._reset_token.used = True
        self._reset_token.save(update_fields=['used'])
        return user


class AdminPasswordResetSerializer(serializers.Serializer):
    new_password = serializers.CharField(write_only=True)

    def validate_new_password(self, value):
        validate_password(value)
        return value
