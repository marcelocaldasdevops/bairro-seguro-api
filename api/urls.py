from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, IncidentViewSet

router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'incidents', IncidentViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
