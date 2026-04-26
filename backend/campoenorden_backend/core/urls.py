from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CampoViewSet, LoteViewSet

router = DefaultRouter()
router.register(r'campos', CampoViewSet)
router.register(r'lotes', LoteViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
