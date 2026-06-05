from django.urls import path

from .views import (
    AcceptInvitationView,
    ActivateAccountView,
    AdminCreateUserView,
    AdminPasswordResetView,
    InviteUserView,
    LogoutView,
    MeView,
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
    # User management
    path('list/', UserListView.as_view(), name='user-list'),
    path('invite/', InviteUserView.as_view(), name='user-invite'),
    path('invite/accept/', AcceptInvitationView.as_view(), name='user-invite-accept'),
    path('create/', AdminCreateUserView.as_view(), name='user-create'),
    path('<int:pk>/reset-password/', AdminPasswordResetView.as_view(), name='user-reset-password'),
]
