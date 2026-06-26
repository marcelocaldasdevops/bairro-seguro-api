from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from .views import UserViewSet, IncidentViewSet

router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'incidents', IncidentViewSet)

urlpatterns = [
    path('users/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('', include(router.urls)),
]
