from rest_framework import serializers
from .models import User, Location, Incident

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'name', 'cpf', 'bairro', 'password', 'is_profile_complete']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user

class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = '__all__'

class IncidentSerializer(serializers.ModelSerializer):
    location = LocationSerializer()

    class Meta:
        model = Incident
        fields = '__all__'
        read_only_fields = ['user']

    def create(self, validated_data):
        location_data = validated_data.pop('location')
        location = Location.objects.create(**location_data)
        incident = Incident.objects.create(location=location, **validated_data)
        return incident

    def validate(self, data):
        user = self.context['request'].user
        if not user.is_profile_complete():
            raise serializers.ValidationError("Seu perfil deve estar completo (Nome, CPF e Bairro) para criar um incidente.")
        return data
