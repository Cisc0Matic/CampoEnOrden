from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import FleteViewSet

router = DefaultRouter()
router.register(r'', FleteViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
