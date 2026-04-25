from collections import Counter
from datetime import timedelta

from rest_framework import serializers
from django.utils import timezone

from .models import (
    Incident,
    IncidentAttachment,
    IncidentComment,
    IncidentConfirmation,
    Location,
    User,
)

class UserSerializer(serializers.ModelSerializer):
    is_profile_complete = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'name', 'cpf', 'bairro', 'password', 'is_profile_complete']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user

    def get_is_profile_complete(self, obj):
        return obj.is_profile_complete()

class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = '__all__'

class IncidentSerializer(serializers.ModelSerializer):
    location = LocationSerializer()
    comments_count = serializers.SerializerMethodField()
    confirmations_count = serializers.SerializerMethodField()
    attachments = serializers.SerializerMethodField()
    user_name = serializers.CharField(source='user.name', read_only=True)
    user_username = serializers.CharField(source='user.username', read_only=True)
    confirmed_by_me = serializers.SerializerMethodField()
    reported_by_me = serializers.SerializerMethodField()

    class Meta:
        model = Incident
        fields = '__all__'
        read_only_fields = ['user']

    def create(self, validated_data):
        location_data = validated_data.pop('location')
        location = Location.objects.create(**location_data)
        validated_data.setdefault('criticality', validated_data.get('severity_level'))
        validated_data.setdefault('bairro', self.context['request'].user.bairro or '')
        incident = Incident.objects.create(location=location, **validated_data)
        return incident

    def validate(self, data):
        user = self.context['request'].user
        if not user.is_profile_complete():
            raise serializers.ValidationError("Seu perfil deve estar completo (Nome, CPF e Bairro) para criar um incidente.")
        if not data.get('title'):
            data['title'] = dict(Incident.CATEGORY_CHOICES).get(data.get('category', 'OUTRO'), 'Ocorrência')
        if data.get('status') == 'RESOLVED' and not data.get('resolved_at'):
            raise serializers.ValidationError({'resolved_at': 'Incidentes resolvidos precisam informar resolved_at.'})
        return data

    def get_comments_count(self, obj):
        return obj.comments.count()

    def get_confirmations_count(self, obj):
        return obj.confirmations.count()

    def get_attachments(self, obj):
        return IncidentAttachmentSerializer(obj.attachments.all(), many=True, context=self.context).data

    def get_confirmed_by_me(self, obj):
        request = self.context.get('request')
        if request is None or not request.user.is_authenticated:
            return False
        return obj.confirmations.filter(user=request.user).exists()

    def get_reported_by_me(self, obj):
        request = self.context.get('request')
        if request is None or not request.user.is_authenticated:
            return False
        return obj.user_id == request.user.id


class IncidentAttachmentSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = IncidentAttachment
        fields = ['id', 'incident', 'file', 'file_url', 'attachment_type', 'created_at']
        read_only_fields = ['incident', 'created_at']

    def get_file_url(self, obj):
        request = self.context.get('request')
        if not obj.file:
          return ''
        if request is not None:
            return request.build_absolute_uri(obj.file.url)
        return obj.file.url


class IncidentCommentSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.name', read_only=True)
    user_username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = IncidentComment
        fields = ['id', 'incident', 'user', 'user_name', 'user_username', 'content', 'created_at']
        read_only_fields = ['incident', 'user', 'created_at']


class IncidentConfirmationSerializer(serializers.ModelSerializer):
    class Meta:
        model = IncidentConfirmation
        fields = ['id', 'incident', 'user', 'created_at']
        read_only_fields = ['incident', 'user', 'created_at']


class DashboardSummarySerializer(serializers.Serializer):
    location_label = serializers.CharField()
    bairro = serializers.CharField()
    status = serializers.CharField()
    safety_percentage = serializers.IntegerField()
    incidents_last_24h = serializers.IntegerField()
    active_watchers = serializers.IntegerField()
    critical_alerts = IncidentSerializer(many=True)
    attention_zones = serializers.ListField(child=serializers.DictField())
    category_breakdown = serializers.DictField()

    @staticmethod
    def from_incidents(user, incidents):
        last_24h = incidents.filter(datetime__gte=timezone.now() - timedelta(hours=24))
        critical_alerts = incidents.filter(criticality='HIGH').order_by('-datetime')[:5]
        by_address = Counter()
        limited_incidents = list(incidents[:100])
        for incident in limited_incidents:
            key = incident.address or incident.reference_point or user.bairro or 'Área monitorada'
            by_address[key] += 1

        attention_zones = []
        for address, total in by_address.most_common(5):
            risk = 'Alto' if total >= 5 else 'Médio' if total >= 3 else 'Baixo'
            attention_zones.append({
                'label': address,
                'incidents_count': total,
                'risk': risk,
            })

        total_incidents = incidents.count()
        if total_incidents >= 12:
            status = 'Crítico'
            safety_percentage = 35
        elif total_incidents >= 6:
            status = 'Moderado'
            safety_percentage = 65
        else:
            status = 'Estável'
            safety_percentage = 84

        category_breakdown = Counter(incidents.values_list('category', flat=True))
        return {
            'location_label': 'Manaus · AM',
            'bairro': user.bairro or 'Área monitorada',
            'status': status,
            'safety_percentage': safety_percentage,
            'incidents_last_24h': last_24h.count(),
            'active_watchers': max(12, total_incidents * 4),
            'critical_alerts': critical_alerts,
            'attention_zones': attention_zones,
            'category_breakdown': dict(category_breakdown),
        }
