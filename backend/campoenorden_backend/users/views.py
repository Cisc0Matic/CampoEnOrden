import logging

from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .emails import (
    send_activation_email,
    send_admin_created_account_email,
    send_invitation_email,
    send_password_reset_email,
)
from .models import EmailVerificationToken, Invitacion, PasswordResetToken, User
from .serializers import (
    AcceptInvitationSerializer,
    ActivateAccountSerializer,
    AdminCreateUserSerializer,
    AdminPasswordResetSerializer,
    InviteUserSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    UpdateProfileSerializer,
    UserSerializer,
)

logger = logging.getLogger(__name__)


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
        else:
            qs = User.objects.select_related('empresa').filter(empresa=request.user.empresa)
        return Response(UserSerializer(qs, many=True).data)


class InviteUserView(APIView):
    permission_classes = [IsAdmin]

    def post(self, request):
        if not request.user.empresa:
            return Response({"detail": "Tu usuario no tiene empresa asignada."}, status=400)
        serializer = InviteUserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        invitation = Invitacion.create(
            email=serializer.validated_data['email'],
            role=serializer.validated_data['role'],
            empresa=request.user.empresa,
            created_by=request.user,
        )
        send_invitation_email(invitation)
        return Response(
            {"detail": f"Invitación enviada a {invitation.email}."},
            status=status.HTTP_201_CREATED,
        )


class AdminCreateUserView(APIView):
    permission_classes = [IsAdmin]

    def post(self, request):
        if not request.user.empresa:
            return Response({"detail": "Tu usuario no tiene empresa asignada."}, status=400)
        serializer = AdminCreateUserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        plain_password = serializer.validated_data['password']
        user = User.objects.create_user(
            username=serializer.validated_data['username'],
            email=serializer.validated_data['email'],
            first_name=serializer.validated_data['first_name'],
            last_name=serializer.validated_data['last_name'],
            dni=serializer.validated_data.get('dni', '') or None,
            password=plain_password,
            role=serializer.validated_data['role'],
            empresa=request.user.empresa,
            is_active=True,
        )
        if user.email:
            send_admin_created_account_email(user, plain_password)
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


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
        return Response({"detail": f"Contraseña de {user.username} actualizada."})


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
