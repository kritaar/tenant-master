from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import logout
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.conf import settings
from django.db.models import Count, Q
from .models import Tenant, Product, TenantUser, ActivityLog
from django.contrib.auth.models import User
import requests
import subprocess
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def is_superuser(user):
    return user.is_superuser

def index(request):
    if request.user.is_authenticated:
        return redirect('panel_dashboard')
    return redirect('login')

def user_logout(request):
    logout(request)
    return redirect('login')

def health_check(request):
    return HttpResponse("OK", status=200)

@login_required
@user_passes_test(is_superuser)
def dashboard(request):
    total_tenants = Tenant.objects.count()
    active_tenants = Tenant.objects.filter(status='active').count()
    shared_tenants = Tenant.objects.filter(type='shared').count()
    dedicated_tenants = Tenant.objects.filter(type='dedicated').count()
    
    recent_tenants = Tenant.objects.select_related('product', 'owner').order_by('-created_at')[:10]
    recent_activity = ActivityLog.objects.select_related('user', 'tenant').order_by('-created_at')[:10]
    
    context = {
        'total_tenants': total_tenants,
        'active_tenants': active_tenants,
        'shared_tenants': shared_tenants,
        'dedicated_tenants': dedicated_tenants,
        'recent_tenants': recent_tenants,
        'recent_activity': recent_activity,
    }
    return render(request, 'panel/dashboard.html', context)

@login_required
@user_passes_test(is_superuser)
def workspaces(request):
    tenants = Tenant.objects.select_related('product', 'owner').all()
    products = Product.objects.filter(is_active=True)
    
    context = {
        'tenants': tenants,
        'products': products,
    }
    return render(request, 'panel/workspaces.html', context)

@login_required
@user_passes_test(is_superuser)
def create_workspace(request):
    if request.method == 'POST':
        try:
            company_name = request.POST.get('company_name')
            subdomain = request.POST.get('subdomain')
            product_id = request.POST.get('product')
            plan = request.POST.get('plan', 'free')
            type_deployment = request.POST.get('type', 'shared')
            owner_username = request.POST.get('owner_username')
            
            if Tenant.objects.filter(subdomain=subdomain).exists():
                messages.error(request, f'El subdominio {subdomain} ya existe')
                return redirect('workspaces')
            
            product = Product.objects.get(id=product_id)
            owner = User.objects.get(username=owner_username)
            
            db_name = f"tenant_{subdomain}"
            
            create_database(db_name)
            
            tenant = Tenant.objects.create(
                name=company_name,
                subdomain=subdomain,
                company_name=company_name,
                product=product,
                plan=plan,
                type=type_deployment,
                db_name=db_name,
                owner=owner,
                status='active'
            )
            
            run_migrations(db_name)
            
            ActivityLog.objects.create(
                tenant=tenant,
                user=request.user,
                action='create',
                description=f'Workspace {company_name} creado',
                ip_address=get_client_ip(request)
            )
            
            messages.success(request, f'Workspace {company_name} creado exitosamente')
            return redirect('workspace_detail', tenant_id=tenant.id)
            
        except Exception as e:
            messages.error(request, f'Error al crear workspace: {str(e)}')
            return redirect('workspaces')
    
    products = Product.objects.filter(is_active=True)
    users = User.objects.filter(is_active=True)
    
    context = {
        'products': products,
        'users': users,
    }
    return render(request, 'panel/create_workspace.html', context)

@login_required
@user_passes_test(is_superuser)
def workspace_detail(request, tenant_id):
    tenant = get_object_or_404(Tenant, id=tenant_id)
    tenant_users = TenantUser.objects.filter(tenant=tenant).select_related('user')
    activity = ActivityLog.objects.filter(tenant=tenant).order_by('-created_at')[:20]
    
    context = {
        'tenant': tenant,
        'tenant_users': tenant_users,
        'activity': activity,
    }
    return render(request, 'panel/workspace_detail.html', context)

@login_required
@user_passes_test(is_superuser)
def workspace_action(request, tenant_id):
    if request.method == 'POST':
        tenant = get_object_or_404(Tenant, id=tenant_id)
        action = request.POST.get('action')
        
        if action == 'suspend':
            tenant.status = 'suspended'
            tenant.save()
            messages.success(request, f'Workspace {tenant.company_name} suspendido')
            
        elif action == 'activate':
            tenant.status = 'active'
            tenant.save()
            messages.success(request, f'Workspace {tenant.company_name} activado')
            
        elif action == 'delete':
            tenant.status = 'inactive'
            tenant.save()
            messages.success(request, f'Workspace {tenant.company_name} eliminado')
            
        ActivityLog.objects.create(
            tenant=tenant,
            user=request.user,
            action=action,
            description=f'Acción {action} ejecutada en {tenant.company_name}',
            ip_address=get_client_ip(request)
        )
        
        return redirect('workspace_detail', tenant_id=tenant.id)
    
    return redirect('workspaces')

@login_required
@user_passes_test(is_superuser)
def clients(request):
    users = User.objects.annotate(
        tenant_count=Count('owned_tenants')
    ).order_by('-date_joined')
    
    context = {
        'users': users,
    }
    return render(request, 'panel/clients.html', context)

@login_required
@user_passes_test(is_superuser)
def deployments(request):
    stacks = []
    
    if settings.PORTAINER_BASE and settings.PORTAINER_API_KEY:
        try:
            stacks = get_portainer_stacks()
        except Exception as e:
            messages.error(request, f'Error al conectar con Portainer: {str(e)}')
    
    context = {
        'stacks': stacks,
        'portainer_configured': bool(settings.PORTAINER_BASE and settings.PORTAINER_API_KEY),
    }
    return render(request, 'panel/deployments.html', context)

@login_required
@user_passes_test(is_superuser)
def sync_deployments(request):
    if request.method == 'POST':
        try:
            stacks = get_portainer_stacks()
            messages.success(request, f'{len(stacks)} stacks sincronizados desde Portainer')
        except Exception as e:
            messages.error(request, f'Error al sincronizar: {str(e)}')
    
    return redirect('deployments')

@login_required
@user_passes_test(is_superuser)
def products(request):
    all_products = Product.objects.all()
    
    context = {
        'products': all_products,
    }
    return render(request, 'panel/products.html', context)

@login_required
@user_passes_test(is_superuser)
def databases(request):
    tenants = Tenant.objects.select_related('product').all()
    
    db_info = []
    for tenant in tenants:
        db_info.append({
            'tenant': tenant,
            'db_name': tenant.db_name,
            'db_host': tenant.db_host,
            'db_port': tenant.db_port,
        })
    
    context = {
        'db_info': db_info,
    }
    return render(request, 'panel/databases.html', context)

@login_required
@user_passes_test(is_superuser)
def activity(request):
    logs = ActivityLog.objects.select_related('user', 'tenant').order_by('-created_at')[:100]
    
    context = {
        'logs': logs,
    }
    return render(request, 'panel/activity.html', context)

@login_required
@user_passes_test(is_superuser)
def settings_view(request):
    context = {
        'panel_domain': settings.PANEL_DOMAIN,
        'base_domain': settings.BASE_DOMAIN,
        'portainer_configured': bool(settings.PORTAINER_BASE and settings.PORTAINER_API_KEY),
    }
    return render(request, 'panel/settings.html', context)

def create_database(db_name):
    conn = psycopg2.connect(
        host=settings.DATABASES['default']['HOST'],
        port=settings.DATABASES['default']['PORT'],
        user=settings.DATABASES['default']['USER'],
        password=settings.DATABASES['default']['PASSWORD'],
        database='postgres'
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()
    
    cursor.execute(f"SELECT 1 FROM pg_database WHERE datname = '{db_name}'")
    exists = cursor.fetchone()
    
    if not exists:
        cursor.execute(f"CREATE DATABASE {db_name}")
    
    cursor.close()
    conn.close()

def run_migrations(db_name):
    pass

def get_portainer_stacks():
    if not settings.PORTAINER_BASE or not settings.PORTAINER_API_KEY:
        return []
    
    url = f"{settings.PORTAINER_BASE}/api/stacks"
    headers = {
        'X-API-Key': settings.PORTAINER_API_KEY
    }
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        return response.json()
    
    return []

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip
