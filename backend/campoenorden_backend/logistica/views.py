from rest_framework import viewsets
from .models import Flete
from .serializers import FleteSerializer

class FleteViewSet(viewsets.ModelViewSet):
    queryset = Flete.objects.all()
    serializer_class = FleteSerializer