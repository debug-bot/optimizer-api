from rest_framework import serializers
from .models import OptimizerFile

class OptimizerFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = OptimizerFile
        fields = ["file"]