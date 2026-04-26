from rest_framework import serializers
from .models import Flete

class FleteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Flete
        fields = '__all__'
