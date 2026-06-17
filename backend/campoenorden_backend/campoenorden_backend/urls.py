from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.response import Response
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from core.views import landing_view
from users.models import User


class CustomTokenObtainPairView(TokenObtainPairView):
    """Distingue cuenta inactiva de credenciales incorrectas."""
    def post(self, request, *args, **kwargs):
        username = request.data.get('username', '')
        try:
            user = User.objects.get(username=username)
            if not user.is_active:
                return Response(
                    {"detail": "cuenta_no_activada"},
                    status=401,
                )
        except User.DoesNotExist:
            pass
        return super().post(request, *args, **kwargs)


urlpatterns = [
    path('', landing_view, name='landing'),
    path('admin/', admin.site.urls),
    path('api/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/users/', include('users.urls')),
    path('api/core/', include('core.urls')),
    path('api/chatbot/', include('chatbot.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
