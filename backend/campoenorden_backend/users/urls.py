from django.urls import path

from .views import (
    AcceptInvitationView,
    ActivateAccountView,
    AdminCreateUserView,
    AdminPasswordResetView,
    AdminUserDetailView,
    AuditLogView,
    EmpresaListView,
    InviteDeleteView,
    InviteListView,
    InviteUserView,
    LogoutView,
    MeView,
    PagoDetailView,
    PagoListView,
    PasswordResetConfirmView,
    PasswordResetRequestView,
    RegisterView,
    ResendActivationView,
    UserListView,
)

urlpatterns = [
    # Auth
    path('auth/register/', RegisterView.as_view(), name='auth-register'),
    path('auth/activate/', ActivateAccountView.as_view(), name='auth-activate'),
    path('auth/resend-activation/', ResendActivationView.as_view(), name='auth-resend-activation'),
    path('auth/logout/', LogoutView.as_view(), name='auth-logout'),
    path('auth/me/', MeView.as_view(), name='auth-me'),
    path('auth/password-reset/', PasswordResetRequestView.as_view(), name='auth-password-reset'),
    path('auth/password-reset/confirm/', PasswordResetConfirmView.as_view(), name='auth-password-reset-confirm'),
    # Gestión de usuarios (admin)
    path('list/', UserListView.as_view(), name='user-list'),
    path('invite/', InviteUserView.as_view(), name='user-invite'),
    path('invite/accept/', AcceptInvitationView.as_view(), name='user-invite-accept'),
    path('invites/', InviteListView.as_view(), name='invite-list'),
    path('invites/<int:pk>/', InviteDeleteView.as_view(), name='invite-delete'),
    path('create/', AdminCreateUserView.as_view(), name='user-create'),
    path('empresas/', EmpresaListView.as_view(), name='empresas-list'),
    path('audit/', AuditLogView.as_view(), name='audit-list'),
    path('pagos/', PagoListView.as_view(), name='pagos-list'),
    path('pagos/<int:pk>/', PagoDetailView.as_view(), name='pagos-detail'),
    path('<int:pk>/reset-password/', AdminPasswordResetView.as_view(), name='user-reset-password'),
    path('<int:pk>/', AdminUserDetailView.as_view(), name='user-detail'),
]