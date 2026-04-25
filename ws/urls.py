from django.urls import path
from . import views

urlpatterns = [
    path('bom-imports/', views.BomImportsView.as_view(), name='bom-imports'),
    path('analysis/<int:pk>/', views.AnalysisDetailView.as_view(), name='analysis-detail'),
    path('stock-and-po-imports/', views.StockAndPoImportsView.as_view(), name='stock-and-po-imports'),
]