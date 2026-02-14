from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    # Registration requires only username, email, password
    # Profile requires name, cpf, bairro for creating incidents
    name = models.CharField(max_length=255, blank=True, null=True)
    cpf = models.CharField(max_length=14, blank=True, null=True)
    bairro = models.CharField(max_length=100, blank=True, null=True)

    def is_profile_complete(self):
        return all([self.name, self.cpf, self.bairro])

    def __str__(self):
        return self.username

class Location(models.Model):
    latitude = models.DecimalField(max_digits=12, decimal_places=9)
    longitude = models.DecimalField(max_digits=12, decimal_places=9)

    def __str__(self):
        return f"({self.latitude}, {self.longitude})"

class Incident(models.Model):
    SEVERITY_CHOICES = [
        ('LOW', 'Baixo'),
        ('MEDIUM', 'Médio'),
        ('HIGH', 'Alto'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='incidents')
    description = models.TextField()
    severity_level = models.CharField(max_length=10, choices=SEVERITY_CHOICES)
    datetime = models.DateTimeField(auto_now_add=True)
    location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name='incidents')

    def __str__(self):
        return f"{self.severity_level} - {self.user.username} - {self.datetime}"
