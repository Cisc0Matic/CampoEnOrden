from rest_framework import viewsets
from .models import Labor
from .serializers import LaborSerializer

class LaborViewSet(viewsets.ModelViewSet):
    queryset = Labor.objects.all()
    serializer_class = LaborSerializer