from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('login/', auth_views.LoginView.as_view(template_name='panel/login.html'), name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('health/', views.health_check, name='health_check'),
    
    path('dashboard/', views.dashboard, name='panel_dashboard'),
    path('workspaces/', views.workspaces, name='workspaces'),
    path('workspaces/create/', views.create_workspace, name='create_workspace'),
    path('workspaces/<int:tenant_id>/', views.workspace_detail, name='workspace_detail'),
    path('workspaces/<int:tenant_id>/action/', views.workspace_action, name='workspace_action'),
    
    path('clients/', views.clients, name='clients'),
    path('deployments/', views.deployments, name='deployments'),
    path('deployments/sync/', views.sync_deployments, name='sync_deployments'),
    path('products/', views.products, name='products'),
    path('databases/', views.databases, name='databases'),
    path('activity/', views.activity, name='activity'),
    path('settings/', views.settings_view, name='settings'),
]
