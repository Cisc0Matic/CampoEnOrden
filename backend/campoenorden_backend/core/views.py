from rest_framework import viewsets
from .models import Campo, Lote
from .serializers import CampoSerializer, LoteSerializer

class CampoViewSet(viewsets.ModelViewSet):
    queryset = Campo.objects.all()
    serializer_class = CampoSerializer

class LoteViewSet(viewsets.ModelViewSet):
    queryset = Lote.objects.all()
    serializer_class = LoteSerializer