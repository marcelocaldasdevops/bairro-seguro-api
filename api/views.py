from django.db.models import Q
from rest_framework import permissions, status, viewsets
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.authtoken.models import Token
from rest_framework_simplejwt.tokens import RefreshToken
from math import radians, cos, sin, asin, sqrt

from .models import Incident, IncidentAttachment, IncidentComment, IncidentConfirmation, Location, User
from .serializers import (
    DashboardSummarySerializer,
    IncidentAttachmentSerializer,
    IncidentCommentSerializer,
    IncidentConfirmationSerializer,
    IncidentSerializer,
    LocationSerializer,
    UserSerializer,
)

def haversine(lon1, lat1, lon2, lat2):
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    r = 6371 # Radius of earth in kilometers
    return c * r

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_permissions(self):
        if self.action in ['create', 'login']:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    @action(detail=False, methods=['get'])
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=['post'], permission_classes=[permissions.AllowAny])
    def login(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        user = User.objects.filter(email=email).first()
        if user and user.check_password(password):
            token, _ = Token.objects.get_or_create(user=user)
            refresh = RefreshToken.for_user(user)
            return Response(
                {
                    'token': str(refresh.access_token),
                    'access': str(refresh.access_token),
                    'refresh': str(refresh),
                    'drf_token': token.key,
                    'user': UserSerializer(user).data,
                }
            )
        return Response({'error': 'Credenciais invalidas'}, status=status.HTTP_400_BAD_REQUEST)

class IncidentViewSet(viewsets.ModelViewSet):
    queryset = Incident.objects.all()
    serializer_class = IncidentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    parser_classes = [JSONParser, FormParser, MultiPartParser]

    def get_queryset(self):
        queryset = (
            Incident.objects.select_related('user', 'location')
            .prefetch_related('comments', 'confirmations')
            .order_by('-datetime')
        )

        category = self.request.query_params.get('category')
        criticality = self.request.query_params.get('criticality')
        bairro = self.request.query_params.get('bairro')
        status_value = self.request.query_params.get('status')

        if category:
            queryset = queryset.filter(category=category)
        if criticality:
            queryset = queryset.filter(criticality=criticality)
        if bairro:
            queryset = queryset.filter(bairro__iexact=bairro)
        if status_value:
            queryset = queryset.filter(status=status_value)
        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def dashboard(self, request):
        lat = request.query_params.get('latitude')
        lon = request.query_params.get('longitude')
        radius = request.query_params.get('radius_km')

        incidents = self.get_queryset()

        if lat and lon and radius:
            try:
                lat = float(lat)
                lon = float(lon)
                radius = float(radius)
                
                lat_deg = radius / 111.0
                lon_deg = radius / (111.0 * abs(cos(radians(lat))))
                
                incidents = incidents.filter(
                    location__latitude__gte=lat - lat_deg,
                    location__latitude__lte=lat + lat_deg,
                    location__longitude__gte=lon - lon_deg,
                    location__longitude__lte=lon + lon_deg
                )
                
                incident_ids = []
                for incident in incidents:
                    dist = haversine(lon, lat, float(incident.location.longitude), float(incident.location.latitude))
                    if dist <= radius:
                        incident_ids.append(incident.id)
                incidents = Incident.objects.filter(id__in=incident_ids).select_related('user', 'location').prefetch_related('comments', 'confirmations').order_by('-datetime')
            except ValueError:
                pass
        elif request.user.bairro:
            incidents = incidents.filter(
                Q(bairro__iexact=request.user.bairro) | Q(user__bairro__iexact=request.user.bairro)
            )

        payload = DashboardSummarySerializer.from_incidents(request.user, incidents)
        serializer = DashboardSummarySerializer(payload)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def feed(self, request):
        queryset = self.get_queryset()
        radius_km = request.query_params.get('radius_km')
        if radius_km:
            queryset = queryset.filter(radius_km__lte=radius_km)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def map(self, request):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        incident = self.get_object()
        confirmation, created = IncidentConfirmation.objects.get_or_create(
            incident=incident,
            user=request.user
        )
        if created:
            return Response({'status': 'confirmed'}, status=status.HTTP_201_CREATED)
        return Response({'status': 'already confirmed'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['delete'])
    def unconfirm(self, request, pk=None):
        incident = self.get_object()
        IncidentConfirmation.objects.filter(incident=incident, user=request.user).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['get', 'post'])
    def comments(self, request, pk=None):
        incident = self.get_object()
        if request.method == 'POST':
            serializer = IncidentCommentSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save(incident=incident, user=request.user)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        comments = incident.comments.all()
        serializer = IncidentCommentSerializer(comments, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def attachments(self, request, pk=None):
        incident = self.get_object()
        serializer = IncidentAttachmentSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save(incident=incident)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
