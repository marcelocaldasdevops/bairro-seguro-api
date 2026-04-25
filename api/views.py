from django.db.models import Q
from rest_framework import permissions, status, viewsets
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.authtoken.models import Token
from rest_framework_simplejwt.tokens import RefreshToken

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
        return Response({'error': 'Credenciais inválidas'}, status=status.HTTP_400_BAD_REQUEST)

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
        incidents = self.get_queryset()
        if request.user.bairro:
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
        serializer = self.get_serializer(queryset[:50], many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def map(self, request):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset[:200], many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def comments(self, request, pk=None):
        incident = self.get_object()
        serializer = IncidentCommentSerializer(incident.comments.select_related('user'), many=True)
        return Response(serializer.data)

    @comments.mapping.post
    def create_comment(self, request, pk=None):
        incident = self.get_object()
        serializer = IncidentCommentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(incident=incident, user=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post', 'delete'], permission_classes=[permissions.IsAuthenticated])
    def confirm(self, request, pk=None):
        incident = self.get_object()
        if request.method.lower() == 'post':
            confirmation, created = IncidentConfirmation.objects.get_or_create(
                incident=incident,
                user=request.user,
            )
            serializer = IncidentConfirmationSerializer(confirmation)
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
            )

        IncidentConfirmation.objects.filter(incident=incident, user=request.user).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['get', 'post'], permission_classes=[permissions.IsAuthenticatedOrReadOnly])
    def attachments(self, request, pk=None):
        incident = self.get_object()
        if request.method.lower() == 'get':
            serializer = IncidentAttachmentSerializer(
                incident.attachments.all(),
                many=True,
                context={'request': request},
            )
            return Response(serializer.data)

        serializer = IncidentAttachmentSerializer(
            data=request.data,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save(incident=incident)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
