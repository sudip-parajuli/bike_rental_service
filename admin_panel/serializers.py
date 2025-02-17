from rest_framework import serializers
from .models import Issue

class AdminPanelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Issue
        fields = '__all__'