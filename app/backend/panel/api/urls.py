from django.urls import path
from . import views

urlpatterns = [
    path('tenants/', views.TenantListCreateView.as_view(), name='api_tenants'),
    path('tenants/<int:pk>/', views.TenantDetailView.as_view(), name='api_tenant_detail'),
    path('tenants/<int:pk>/convert/', views.ConvertTenantView.as_view(), name='api_convert_tenant'),
    path('products/', views.ProductListView.as_view(), name='api_products'),
    path('deployments/sync/', views.SyncDeploymentsView.as_view(), name='api_sync_deployments'),
]
