from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from .models import Incident, IncidentAttachment, IncidentConfirmation, Location, User


class BaseApiTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='marcelo',
            email='marcelo@example.com',
            password='12345678',
            name='Marcelo',
            cpf='123.456.789-00',
            bairro='Jorge Teixeira',
        )
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')


class AuthenticationTests(APITestCase):
    def test_login_success(self):
        user = User.objects.create_user(
            username='tester',
            email='tester@example.com',
            password='12345678',
        )

        response = self.client.post(
            '/api/users/login/',
            {'email': user.email, 'password': '12345678'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)

    def test_login_failure(self):
        User.objects.create_user(
            username='tester',
            email='tester@example.com',
            password='12345678',
        )

        response = self.client.post(
            '/api/users/login/',
            {'email': 'tester@example.com', 'password': 'senha-errada'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class IncidentApiTests(BaseApiTestCase):
    def test_create_incident_with_enriched_fields(self):
        payload = {
            'title': 'Assalto próximo ao ponto',
            'description': 'Dois suspeitos em uma motocicleta preta.',
            'category': 'ASSALTO',
            'severity_level': 'HIGH',
            'criticality': 'HIGH',
            'status': 'OPEN',
            'is_emergency': True,
            'bairro': 'Jorge Teixeira',
            'address': 'Rua das Flores, 452',
            'reference_point': 'Próximo ao mercadinho',
            'radius_km': '1.0',
            'location': {
                'latitude': '-3.101944000',
                'longitude': '-59.974167000',
            },
        }

        response = self.client.post('/api/incidents/', payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        incident = Incident.objects.get()
        self.assertEqual(incident.category, 'ASSALTO')
        self.assertEqual(incident.bairro, 'Jorge Teixeira')
        self.assertEqual(incident.address, 'Rua das Flores, 452')

    def test_create_incident_requires_complete_profile(self):
        incomplete = User.objects.create_user(
            username='incomplete',
            email='incomplete@example.com',
            password='12345678',
        )
        token = Token.objects.create(user=incomplete)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')

        response = self.client.post(
            '/api/incidents/',
            {
                'description': 'Teste',
                'category': 'OUTRO',
                'severity_level': 'LOW',
                'location': {'latitude': '-3.1', 'longitude': '-59.9'},
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('non_field_errors', response.data)

    def test_feed_filters_by_category(self):
        low_location = Location.objects.create(latitude='-3.11', longitude='-59.91')
        high_location = Location.objects.create(latitude='-3.12', longitude='-59.92')
        Incident.objects.create(
            user=self.user,
            title='Poste apagado',
            description='Sem iluminação',
            category='INFRAESTRUTURA',
            severity_level='LOW',
            criticality='LOW',
            bairro='Jorge Teixeira',
            location=low_location,
        )
        Incident.objects.create(
            user=self.user,
            title='Assalto',
            description='Ocorrência crítica',
            category='ASSALTO',
            severity_level='HIGH',
            criticality='HIGH',
            bairro='Jorge Teixeira',
            location=high_location,
        )

        response = self.client.get('/api/incidents/feed/?category=ASSALTO')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['category'], 'ASSALTO')

    def test_map_returns_results(self):
        location = Location.objects.create(latitude='-3.11', longitude='-59.91')
        Incident.objects.create(
            user=self.user,
            title='Assalto',
            description='Ocorrência crítica',
            category='ASSALTO',
            severity_level='HIGH',
            criticality='HIGH',
            bairro='Jorge Teixeira',
            location=location,
        )

        response = self.client.get('/api/incidents/map/?criticality=HIGH')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['category'], 'ASSALTO')

    def test_dashboard_returns_summary(self):
        location = Location.objects.create(latitude='-3.10', longitude='-59.97')
        Incident.objects.create(
            user=self.user,
            title='Assalto',
            description='Ocorrência crítica',
            category='ASSALTO',
            severity_level='HIGH',
            criticality='HIGH',
            bairro='Jorge Teixeira',
            address='Rua 1',
            location=location,
        )

        response = self.client.get('/api/incidents/dashboard/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['bairro'], 'Jorge Teixeira')
        self.assertIn('critical_alerts', response.data)
        self.assertIn('attention_zones', response.data)

    def test_comment_and_confirmation_flow(self):
        incident = Incident.objects.create(
            user=self.user,
            title='Assalto',
            description='Ocorrência crítica',
            category='ASSALTO',
            severity_level='HIGH',
            criticality='HIGH',
            bairro='Jorge Teixeira',
            location=Location.objects.create(latitude='-3.15', longitude='-59.95'),
        )

        comment_response = self.client.post(
            f'/api/incidents/{incident.id}/comments/',
            {'content': 'Vi a movimentação no local.'},
            format='json',
        )
        confirm_response = self.client.post(f'/api/incidents/{incident.id}/confirm/')

        self.assertEqual(comment_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(confirm_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(IncidentConfirmation.objects.filter(incident=incident).count(), 1)

        comments_response = self.client.get(f'/api/incidents/{incident.id}/comments/')
        self.assertEqual(comments_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(comments_response.data), 1)

        detail_response = self.client.get(f'/api/incidents/{incident.id}/')
        self.assertEqual(detail_response.status_code, status.HTTP_200_OK)
        self.assertTrue(detail_response.data['confirmed_by_me'])

    def test_attachment_upload_flow(self):
        incident = Incident.objects.create(
            user=self.user,
            title='Assalto',
            description='Ocorrência com evidência',
            category='ASSALTO',
            severity_level='HIGH',
            criticality='HIGH',
            bairro='Jorge Teixeira',
            location=Location.objects.create(latitude='-3.16', longitude='-59.96'),
        )

        upload = SimpleUploadedFile(
            'evidencia.jpg',
            b'fake-image-content',
            content_type='image/jpeg',
        )

        response = self.client.post(
            f'/api/incidents/{incident.id}/attachments/',
            {'file': upload, 'attachment_type': 'IMAGE'},
            format='multipart',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(IncidentAttachment.objects.filter(incident=incident).count(), 1)

        details_response = self.client.get(f'/api/incidents/{incident.id}/')
        self.assertEqual(details_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(details_response.data['attachments']), 1)
