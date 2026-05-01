from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CampoViewSet, PersonaViewSet, CampanaViewSet, LoteViewSet,
    CultivoViewSet, InsumoViewSet, LaborViewSet, FleteViewSet,
    DocumentoViewSet, ParametroViewSet, dashboard, indicadores_campo,
    lista_campos, lista_lotes, lista_labores, lista_fletes, lista_documentos
)

router = DefaultRouter()
router.register(r'campos', CampoViewSet)
router.register(r'personas', PersonaViewSet)
router.register(r'campanas', CampanaViewSet)
router.register(r'lotes', LoteViewSet)
router.register(r'cultivos', CultivoViewSet)
router.register(r'insumos', InsumoViewSet)
router.register(r'labores', LaborViewSet)
router.register(r'fletes', FleteViewSet)
router.register(r'documentos', DocumentoViewSet)
router.register(r'parametros', ParametroViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('dashboard/', dashboard, name='dashboard'),
    path('dashboard/campo/<int:campo_id>/', indicadores_campo, name='indicadores-campo'),
    path('lista/campos/', lista_campos, name='lista-campos'),
    path('lista/lotes/', lista_lotes, name='lista-lotes'),
    path('lista/labores/', lista_labores, name='lista-labores'),
    path('lista/fletes/', lista_fletes, name='lista-fletes'),
    path('lista/documentos/', lista_documentos, name='lista-documentos'),
]