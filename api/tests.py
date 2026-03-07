from django.test import TestCase

# Create your tests here.
from django.contrib.auth.models import User
from django.urls import reverse

class LoginTest(TestCase):
    def setUp(self):
        self.username = 'testuser'
        self.password = 'testpassword123'
        self.user = User.objects.create_user(username=self.username, password=self.password)
        self.login_url = reverse('login')

    def test_login_success(self):
        response = self.client.post(self.login_url, {
            'username': self.username,
            'password': self.password
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue('_auth_user_id' in self.client.session)

    def test_login_failure(self):
        response = self.client.post(self.login_url, {
            'username': self.username,
            'password': 'wrongpassword'
        })
        self.assertFalse('_auth_user_id' in self.client.session)
