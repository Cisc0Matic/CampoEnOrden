from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import LaborViewSet

router = DefaultRouter()
router.register(r'', LaborViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
