from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('login/', auth_views.LoginView.as_view(template_name='panel/login.html'), name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('health/', views.health_check, name='health_check'),
    
    # Dashboard
    path('dashboard/', views.dashboard, name='panel_dashboard'),
    
    # Workspaces CRUD
    path('workspaces/', views.workspaces, name='workspaces'),
    path('workspaces/create/', views.create_workspace, name='create_workspace'),
    path('workspaces/<int:tenant_id>/', views.workspace_detail, name='workspace_detail'),
    path('workspaces/<int:tenant_id>/edit/', views.edit_workspace, name='edit_workspace'),
    path('workspaces/<int:tenant_id>/action/', views.workspace_action, name='workspace_action'),
    path('workspaces/<int:tenant_id>/users/', views.manage_workspace_users, name='manage_workspace_users'),
    path('workspaces/<int:tenant_id>/create-repo/', views.create_workspace_repo, name='create_workspace_repo'),
    
    # Otros módulos
    path('clients/', views.clients, name='clients'),
    path('deployments/', views.deployments, name='deployments'),
    path('products/', views.products, name='products'),
    path('products/create/', views.create_product, name='create_product'),
    path('databases/', views.databases, name='databases'),
    path('databases/<str:db_name>/', views.database_manage, name='database_manage'),
    path('databases/<str:db_name>/users/', views.database_users_api, name='database_users_api'),
    path('activity/', views.activity, name='activity'),
    path('settings/', views.settings_view, name='settings'),
]