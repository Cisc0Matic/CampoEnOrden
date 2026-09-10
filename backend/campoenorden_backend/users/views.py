import logging

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import Q
from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from core.models import Persona
from .emails import (
    send_activation_email,
    send_admin_created_account_email,
    send_invitation_email,
    send_password_reset_email,
)
from .models import (
    EmailVerificationToken,
    Invitacion,
    PasswordResetToken,
    Pago,
    User,
    UserAuditLog,
)
from .serializers import (
    AcceptInvitationSerializer,
    ActivateAccountSerializer,
    AdminCreateUserSerializer,
    AdminPasswordResetSerializer,
    AdminUpdateUserSerializer,
    AuditLogSerializer,
    EmpresaSerializer,
    InviteListSerializer,
    InviteUserSerializer,
    PagoSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    UpdateProfileSerializer,
    UserSerializer,
)

logger = logging.getLogger(__name__)

BASIC_ROLES = [User.Role.OPERARIO, User.Role.CONSULTA, User.Role.PRODUCTOR]


class IsAdmin(IsAuthenticated):
    def has_permission(self, request, view):
        return (
            super().has_permission(request, view)
            and request.user.role in [User.Role.ADMIN_PRINCIPAL, User.Role.ADMIN_EMPRESA]
        )


class IsAdminPrincipal(IsAdmin):
    def has_permission(self, request, view):
        return super().has_permission(request, view) and request.user.role == User.Role.ADMIN_PRINCIPAL


def log_action(actor, action, target_type=None, target_id=None, target_desc=None, payload=None):
    """Registra una acción administrativa en la bitácora de auditoría."""
    try:
        UserAuditLog.objects.create(
            actor=actor,
            action=action,
            target_type=target_type or '',
            target_id=str(target_id) if target_id is not None else '',
            target_desc=target_desc or '',
            payload=payload or {},
        )
    except Exception:
        logger.exception("FALLO al registrar bitácora de auditoría")


class IsAdmin(IsAuthenticated):
    def has_permission(self, request, view):
        return (
            super().has_permission(request, view)
            and request.user.role in [User.Role.ADMIN_PRINCIPAL, User.Role.ADMIN_EMPRESA]
        )


# ─── Registro y activación ────────────────────────────────────────────────────

class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        from .serializers import RegisterSerializer
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.create(serializer.validated_data)
        token_obj = EmailVerificationToken.create_for_user(user)
        try:
            send_activation_email(user, token_obj.token)
            logger.info("Email de activación enviado a %s", user.email)
        except Exception:
            logger.exception("FALLO email de activación a %s", user.email)
        return Response(
            {"detail": f"Cuenta creada. Revisá {user.email} para activar tu cuenta."},
            status=status.HTTP_201_CREATED,
        )


class ActivateAccountView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ActivateAccountSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "Cuenta activada. Ya podés iniciar sesión."})


class ResendActivationView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        # Acepta email o username
        identifier = request.data.get('email') or request.data.get('username', '')
        try:
            if '@' in identifier:
                user = User.objects.get(email=identifier, is_active=False)
            else:
                user = User.objects.get(username=identifier, is_active=False)
        except User.DoesNotExist:
            # No revelar si existe o no
            return Response({"detail": "Si la cuenta existe y no está activada, recibirás el email."})
        token_obj = EmailVerificationToken.create_for_user(user)
        try:
            send_activation_email(user, token_obj.token)
        except Exception:
            logger.exception("FALLO reenvío de activación a %s", user.email)
            return Response(
                {"detail": "No se pudo enviar el email. Intentá de nuevo en unos minutos."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        return Response({"detail": "Email de activación reenviado."})


# ─── Perfil propio ────────────────────────────────────────────────────────────

class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)

    def patch(self, request):
        serializer = UpdateProfileSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(UserSerializer(request.user).data)


# ─── Gestión de usuarios (admin) ──────────────────────────────────────────────

class UserListView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        if request.user.role == User.Role.ADMIN_PRINCIPAL:
            qs = User.objects.select_related('empresa').all()
            emp = request.query_params.get('empresa', '')
            if emp.isdigit():
                qs = qs.filter(empresa_id=int(emp))
        else:
            qs = User.objects.select_related('empresa').filter(empresa=request.user.empresa)
        return Response(UserSerializer(qs, many=True).data)


class InviteUserView(APIView):
    permission_classes = [IsAdmin]

    def post(self, request):
        serializer = InviteUserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        is_principal = request.user.role == User.Role.ADMIN_PRINCIPAL

        try:
            empresa = self._resolver_empresa(request, data.get('empresa_id'), is_principal)
        except ValidationError as exc:
            return Response({"detail": exc.detail}, status=exc.status_code)

        role = data['role']
        if not is_principal and role not in BASIC_ROLES:
            raise ValidationError({"role": "Como administrador de empresa solo podés crear los roles OPERARIO, CONSULTA y PRODUCTOR."})

        invitation = Invitacion.create(
            email=data['email'],
            role=role,
            empresa=empresa,
            created_by=request.user,
        )
        send_invitation_email(invitation)
        log_action(
            request.user, 'INVITE_USER',
            target_type='user', target_id=None, target_desc=data['email'],
            payload={'role': role, 'empresa_id': empresa.id if empresa else None},
        )
        return Response(
            {"detail": f"Invitación enviada a {invitation.email}."},
            status=status.HTTP_201_CREATED,
        )

    def _resolver_empresa(self, request, empresa_id, is_principal):
        """Resuelve la empresa destino de la invitación/creación según el actor."""
        if not is_principal:
            if not request.user.empresa:
                raise ValidationError({"detail": "Tu usuario no tiene empresa asignada."})
            return request.user.empresa
        empresa = None
        if empresa_id:
            try:
                empresa = Persona.objects.get(pk=empresa_id, tipo=Persona.TipoPersona.EMPRESA)
            except Persona.DoesNotExist:
                raise ValidationError({"empresa_id": "La empresa indicada no existe."})
        elif request.user.empresa:
            empresa = request.user.empresa
        if not empresa:
            raise ValidationError({"empresa_id": "El ADMIN_PRINCIPAL sin empresa propia debe indicar empresa_id."})
        return empresa


class AdminCreateUserView(APIView):
    permission_classes = [IsAdmin]

    def post(self, request):
        serializer = AdminCreateUserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        is_principal = request.user.role == User.Role.ADMIN_PRINCIPAL

        empresa = self._resolver_empresa(request, data.get('empresa_id'), is_principal)

        role = data['role']
        if not is_principal and role not in BASIC_ROLES:
            raise ValidationError({"role": "Como administrador de empresa solo podés crear los roles OPERARIO, CONSULTA y PRODUCTOR."})

        plain_password = data['password']
        user = User.objects.create_user(
            username=data['username'],
            email=data['email'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            dni=data.get('dni', '') or None,
            password=plain_password,
            role=role,
            empresa=empresa,
            is_active=True,
        )
        if user.email:
            send_admin_created_account_email(user, plain_password)
        if role == User.Role.PRODUCTOR:
            user.vincular_productor()
        log_action(
            request.user, 'CREATE_USER',
            target_type='user', target_id=user.id, target_desc=user.username,
            payload={'role': role, 'empresa_id': empresa.id if empresa else None, 'email': user.email},
        )
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)

    def _resolver_empresa(self, request, empresa_id, is_principal):
        return InviteUserView()._resolver_empresa(request, empresa_id, is_principal)


class AdminPasswordResetView(APIView):
    permission_classes = [IsAdmin]

    def post(self, request, pk):
        filter_kwargs = {'pk': pk}
        if request.user.role != User.Role.ADMIN_PRINCIPAL:
            filter_kwargs['empresa'] = request.user.empresa
        try:
            user = User.objects.get(**filter_kwargs)
        except User.DoesNotExist:
            return Response({"detail": "Usuario no encontrado."}, status=404)
        serializer = AdminPasswordResetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_password = serializer.validated_data['new_password']
        user.set_password(new_password)
        user.save(update_fields=['password'])
        if user.email:
            send_admin_created_account_email(user, new_password)
        log_action(
            request.user, 'RESET_PASSWORD',
            target_type='user', target_id=user.id, target_desc=user.username,
        )
        return Response({"detail": f"Contraseña de {user.username} actualizada."})


class AdminUserDetailView(APIView):
    """PATCH de un usuario (rol/empresa/activo/datos) desde el panel de administración."""

    permission_classes = [IsAdmin]

    def get_object(self, request, pk):
        if request.user.role == User.Role.ADMIN_PRINCIPAL:
            try:
                return User.objects.select_related('empresa').get(pk=pk)
            except User.DoesNotExist:
                return None
        try:
            return User.objects.select_related('empresa').get(pk=pk, empresa=request.user.empresa)
        except User.DoesNotExist:
            return None

    def patch(self, request, pk):
        user = self.get_object(request, pk)
        if user is None:
            return Response({"detail": "Usuario no encontrado."}, status=404)
        if request.user.role == User.Role.ADMIN_PRINCIPAL and user.role == User.Role.ADMIN_PRINCIPAL and user.pk != request.user.pk:
            return Response({"detail": "No podés modificar a otro ADMIN_PRINCIPAL."}, status=403)

        serializer = AdminUpdateUserSerializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        if request.user.role == User.Role.ADMIN_EMPRESA:
            if data.get('role') not in BASIC_ROLES:
                raise ValidationError({"role": "Como administrador de empresa solo podés asignar los roles OPERARIO, CONSULTA y PRODUCTOR."})
            data.pop('empresa', None)

        if data.get('role') == User.Role.ADMIN_PRINCIPAL:
            raise ValidationError({"role": "No se puede asignar el rol ADMIN_PRINCIPAL de esta forma."})

        changed = {k: v for k, v in data.items()}
        serializer.save()
        if user.role == User.Role.PRODUCTOR:
            user.vincular_productor()
        log_action(
            request.user, 'UPDATE_USER',
            target_type='user', target_id=user.id, target_desc=user.username,
            payload={k: (v.nombre if isinstance(v, Persona) else str(v)) for k, v in changed.items()},
        )
        return Response(UserSerializer(user).data)


class EmpresaListView(APIView):
    """Listado/creación de empresas (Personas tipo EMPRESA). Solo ADMIN_PRINCIPAL."""

    permission_classes = [IsAdminPrincipal]

    def get(self, request):
        qs = Persona.objects.filter(tipo=Persona.TipoPersona.EMPRESA).order_by('nombre')
        return Response(EmpresaSerializer(qs, many=True).data)

    def post(self, request):
        serializer = EmpresaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        empresa = serializer.save()
        log_action(
            request.user, 'CREATE_EMPRESA',
            target_type='empresa', target_id=empresa.id, target_desc=empresa.nombre,
        )
        return Response(EmpresaSerializer(empresa).data, status=status.HTTP_201_CREATED)


class EmpresaDetailView(APIView):
    """Detalle y edición de una empresa (Persona tipo EMPRESA). Solo ADMIN_PRINCIPAL."""

    permission_classes = [IsAdminPrincipal]

    EDITABLES = ['nombre', 'documento', 'direccion', 'telefono', 'email', 'observaciones', 'activo']

    def get_object(self, pk):
        try:
            return Persona.objects.get(pk=pk, tipo=Persona.TipoPersona.EMPRESA)
        except (Persona.DoesNotExist, ValueError):
            return None

    def get(self, request, pk):
        empresa = self.get_object(pk)
        if empresa is None:
            return Response({"detail": "Empresa no encontrada."}, status=404)
        return Response(EmpresaSerializer(empresa).data)

    def patch(self, request, pk):
        empresa = self.get_object(pk)
        if empresa is None:
            return Response({"detail": "Empresa no encontrada."}, status=404)
        serializer = EmpresaSerializer(empresa, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        changed = {k: v for k, v in serializer.validated_data.items() if k in self.EDITABLES}
        if changed:
            for k, v in changed.items():
                setattr(empresa, k, v)
            empresa.save(update_fields=list(changed.keys()))
            log_action(
                request.user, 'UPDATE_EMPRESA',
                target_type='empresa', target_id=empresa.id, target_desc=empresa.nombre,
                payload={k: str(v) for k, v in changed.items()},
            )
        return Response(EmpresaSerializer(empresa).data)


class InviteListView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        qs = Invitacion.objects.select_related('empresa').filter(accepted_at__isnull=True).order_by('-created_at')
        if request.user.role == User.Role.ADMIN_EMPRESA:
            qs = qs.filter(empresa=request.user.empresa)
        return Response(InviteListSerializer(qs, many=True).data)


class InviteDeleteView(APIView):
    permission_classes = [IsAdmin]

    def delete(self, request, pk):
        if request.user.role == User.Role.ADMIN_PRINCIPAL:
            qs = Invitacion.objects.all()
        else:
            qs = Invitacion.objects.filter(empresa=request.user.empresa)
        try:
            invite = qs.get(pk=pk)
        except Invitacion.DoesNotExist:
            return Response({"detail": "Invitación no encontrada."}, status=404)
        invite.delete()
        log_action(
            request.user, 'DELETE_INVITE',
            target_type='invite', target_id=invite.id, target_desc=invite.email,
        )
        return Response(status=status.HTTP_204_NO_CONTENT)


class AuditLogView(APIView):
    permission_classes = [IsAdminPrincipal]

    def get(self, request):
        qs = UserAuditLog.objects.select_related('actor').all()
        limit = request.query_params.get('limit', 200)
        try:
            limit = max(1, min(int(limit), 1000))
        except (TypeError, ValueError):
            limit = 200
        return Response(AuditLogSerializer(qs[:limit], many=True).data)


class PagoListView(APIView):
    permission_classes = [IsAdminPrincipal]

    def get(self, request):
        qs = Pago.objects.select_related('empresa', 'registrado_por').all()
        empresa_id = request.query_params.get('empresa')
        if empresa_id:
            qs = qs.filter(empresa_id=empresa_id)
        return Response(PagoSerializer(qs, many=True).data)

    def post(self, request):
        serializer = PagoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        pago = serializer.save(registrado_por=request.user)
        log_action(
            request.user, 'CREATE_PAGO',
            target_type='pago', target_id=pago.id,
            target_desc=pago.empresa.nombre if pago.empresa else None,
            payload={'monto': str(pago.monto), 'moneda': pago.moneda, 'concepto': pago.concepto},
        )
        return Response(PagoSerializer(pago).data, status=status.HTTP_201_CREATED)


class PagoDetailView(APIView):
    permission_classes = [IsAdminPrincipal]

    def get_object(self, pk):
        try:
            return Pago.objects.get(pk=pk)
        except Pago.DoesNotExist:
            return None

    def patch(self, request, pk):
        pago = self.get_object(pk)
        if pago is None:
            return Response({"detail": "Pago no encontrado."}, status=404)
        serializer = PagoSerializer(pago, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        pago = serializer.save()
        log_action(
            request.user, 'UPDATE_PAGO',
            target_type='pago', target_id=pago.id,
            target_desc=pago.empresa.nombre if pago.empresa else None,
        )
        return Response(PagoSerializer(pago).data)

    def delete(self, request, pk):
        pago = self.get_object(pk)
        if pago is None:
            return Response({"detail": "Pago no encontrado."}, status=404)
        pago.delete()
        log_action(
            request.user, 'DELETE_PAGO',
            target_type='pago', target_id=pago.id,
            target_desc=pago.empresa.nombre if pago.empresa else None,
        )
        return Response(status=status.HTTP_204_NO_CONTENT)


# ─── Invitaciones (flujo público) ─────────────────────────────────────────────

class AcceptInvitationView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        token = request.query_params.get('token', '')
        try:
            inv = Invitacion.objects.select_related('empresa').get(token=token)
        except Invitacion.DoesNotExist:
            return Response({"detail": "Token inválido."}, status=400)
        if not inv.is_valid:
            return Response({"detail": "La invitación ya fue usada o expiró."}, status=400)
        return Response({
            "email": inv.email,
            "role": inv.role,
            "role_display": inv.get_role_display(),
            "empresa": inv.empresa.nombre,
        })

    def post(self, request):
        serializer = AcceptInvitationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"detail": "Cuenta creada. Ya podés iniciar sesión."},
            status=status.HTTP_201_CREATED,
        )


# ─── Recuperación de contraseña ───────────────────────────────────────────────

class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if serializer.user:
            token_obj = PasswordResetToken.create_for_user(serializer.user)
            try:
                send_password_reset_email(serializer.user, token_obj.token)
            except Exception:
                logger.exception("FALLO email de password reset a %s", serializer.user.email)
        return Response({"detail": "Si el email existe, recibirás las instrucciones en breve."})


class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "Contraseña actualizada. Ya podés iniciar sesión."})


# ─── Logout ───────────────────────────────────────────────────────────────────

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")
            if refresh_token:
                RefreshToken(refresh_token).blacklist()
        except Exception:
            pass
        return Response({"detail": "Sesión cerrada."})
