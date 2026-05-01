from rest_framework import serializers
from .models import Labor

class LaborSerializer(serializers.ModelSerializer):
    class Meta:
        model = Labor
        fields = '__all__'
