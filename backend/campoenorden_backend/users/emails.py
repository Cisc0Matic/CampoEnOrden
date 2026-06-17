from django.conf import settings
from django.core.mail import send_mail

FRONTEND_URL = getattr(settings, 'FRONTEND_URL', 'http://localhost:8100')


def send_activation_email(user, token):
    link = f"{FRONTEND_URL}/activate?token={token}"
    send_mail(
        subject="Activá tu cuenta en CampoEnOrden",
        message=(
            f"Hola {user.first_name or user.username},\n\n"
            f"Tu usuario es: {user.username}\n\n"
            f"Para activar tu cuenta hacé click en el siguiente enlace:\n{link}\n\n"
            f"El enlace expira en 24 horas.\n\n"
            f"Si no creaste una cuenta en CampoEnOrden, ignorá este email.\n\n"
            f"Saludos,\nEl equipo de CampoEnOrden"
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
    )


def send_invitation_email(invitation):
    link = f"{FRONTEND_URL}/invite?token={invitation.token}"
    role_display = invitation.get_role_display()
    send_mail(
        subject=f"Te invitaron a CampoEnOrden — {invitation.empresa.nombre}",
        message=(
            f"Hola,\n\n"
            f"Fuiste invitado/a a unirte a CampoEnOrden como {role_display} "
            f"en {invitation.empresa.nombre}.\n\n"
            f"Para crear tu cuenta hacé click en el siguiente enlace:\n{link}\n\n"
            f"El enlace expira en 48 horas.\n\n"
            f"Si no esperabas esta invitación, ignorá este email.\n\n"
            f"Saludos,\nEl equipo de CampoEnOrden"
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[invitation.email],
    )


def send_admin_created_account_email(user, plain_password):
    link = f"{FRONTEND_URL}/login"
    send_mail(
        subject="Tu cuenta en CampoEnOrden fue creada",
        message=(
            f"Hola {user.first_name or user.username},\n\n"
            f"Un administrador creó una cuenta para vos en CampoEnOrden.\n\n"
            f"Tus credenciales de acceso son:\n"
            f"  Usuario: {user.username}\n"
            f"  Contraseña: {plain_password}\n\n"
            f"Ingresá en: {link}\n\n"
            f"Te recomendamos cambiar tu contraseña al ingresar por primera vez.\n\n"
            f"Saludos,\nEl equipo de CampoEnOrden"
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
    )


def send_password_reset_email(user, token):
    link = f"{FRONTEND_URL}/reset-password?token={token}"
    send_mail(
        subject="Restablecer contraseña — CampoEnOrden",
        message=(
            f"Hola {user.first_name or user.username},\n\n"
            f"Tu usuario es: {user.username}\n\n"
            f"Recibimos una solicitud para restablecer la contraseña de tu cuenta.\n\n"
            f"Hacé click en el siguiente enlace para elegir una nueva contraseña:\n{link}\n\n"
            f"El enlace expira en 1 hora. Si no solicitaste el cambio, ignorá este email.\n\n"
            f"Saludos,\nEl equipo de CampoEnOrden"
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
    )
