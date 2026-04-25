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
    CATEGORY_CHOICES = [
        ('ASSALTO', 'Assalto'),
        ('ACIDENTE', 'Acidente'),
        ('SUSPEITO', 'Suspeito'),
        ('INFRAESTRUTURA', 'Infraestrutura'),
        ('OUTRO', 'Outro'),
    ]

    SEVERITY_CHOICES = [
        ('LOW', 'Baixo'),
        ('MEDIUM', 'Médio'),
        ('HIGH', 'Alto'),
    ]

    STATUS_CHOICES = [
        ('OPEN', 'Aberto'),
        ('UNDER_REVIEW', 'Em análise'),
        ('RESOLVED', 'Resolvido'),
        ('DISMISSED', 'Descartado'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='incidents')
    title = models.CharField(max_length=255, blank=True)
    description = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='OUTRO')
    severity_level = models.CharField(max_length=10, choices=SEVERITY_CHOICES)
    criticality = models.CharField(max_length=10, choices=SEVERITY_CHOICES, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='OPEN')
    is_emergency = models.BooleanField(default=False)
    bairro = models.CharField(max_length=100, blank=True)
    address = models.CharField(max_length=255, blank=True)
    reference_point = models.CharField(max_length=255, blank=True)
    radius_km = models.DecimalField(max_digits=4, decimal_places=1, default=1.0)
    datetime = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(blank=True, null=True)
    location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name='incidents')

    def __str__(self):
        return f"{self.severity_level} - {self.user.username} - {self.datetime}"

    @property
    def comments_count(self):
        return self.comments.count()

    @property
    def confirmations_count(self):
        return self.confirmations.count()


class IncidentComment(models.Model):
    incident = models.ForeignKey(Incident, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='incident_comments')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Comment {self.id} - {self.user.username}"


class IncidentConfirmation(models.Model):
    incident = models.ForeignKey(Incident, on_delete=models.CASCADE, related_name='confirmations')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='incident_confirmations')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['incident', 'user'],
                name='unique_incident_confirmation_per_user',
            ),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"Confirmation {self.id} - {self.user.username}"


class IncidentAttachment(models.Model):
    ATTACHMENT_TYPE_CHOICES = [
        ('IMAGE', 'Imagem'),
        ('VIDEO', 'Vídeo'),
        ('OTHER', 'Outro'),
    ]

    incident = models.ForeignKey(Incident, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='incident_attachments/')
    attachment_type = models.CharField(max_length=10, choices=ATTACHMENT_TYPE_CHOICES, default='IMAGE')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Attachment {self.id} - {self.attachment_type}"
