from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken


class WsJWTAuthenticationTests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="admin",
            email="admin@admin.com",
            password="admin123",
        )
        self.access_token = str(RefreshToken.for_user(self.user).access_token)

    def test_ws_endpoint_accepts_jwt_from_query_string(self):
        response = self.client.get(
            f"{reverse('bom-imports')}?token={self.access_token}"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_ws_endpoint_accepts_jwt_from_authorization_header(self):
        response = self.client.get(
            reverse('stock-and-po-imports'),
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
