"""
Views del Panel de Administración Tenant Master
Con gestión de usuarios por producto
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import logout
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.conf import settings
from django.db.models import Count
from django.db import connection
from .models import Tenant, Product, TenantUser, ActivityLog
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import secrets
import string
import subprocess
import json
import shutil
import os


def is_superuser(user):
    return user.is_superuser


def generate_password(length=32):
    """Genera contraseña segura"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


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
    """Dashboard principal"""
    try:
        total_tenants = Tenant.objects.count()
        active_tenants = Tenant.objects.filter(status='active').count()
        
        dedicated_count = Tenant.objects.filter(type='dedicated').count()
        shared_count = Tenant.objects.filter(type='shared').count()
        
        recent_tenants = Tenant.objects.select_related('product', 'owner').order_by('-created_at')[:10]
        recent_activity = ActivityLog.objects.select_related('user', 'tenant').order_by('-created_at')[:10]
        
        context = {
            'total_tenants': total_tenants,
            'active_tenants': active_tenants,
            'dedicated_count': dedicated_count,
            'shared_count': shared_count,
            'recent_tenants': recent_tenants,
            'recent_activity': recent_activity,
        }
        return render(request, 'panel/dashboard.html', context)
    except Exception as e:
        messages.error(request, f'Error al cargar dashboard: {str(e)}')
        return render(request, 'panel/dashboard.html', {'error': str(e)})


@login_required
@user_passes_test(is_superuser)
def workspaces(request):
    """Lista de workspaces"""
    try:
        tenants = Tenant.objects.select_related('product', 'owner').all()
        products = Product.objects.filter(is_active=True)
        
        context = {
            'tenants': tenants,
            'products': products,
        }
        return render(request, 'panel/workspaces.html', context)
    except Exception as e:
        messages.error(request, f'Error al cargar workspaces: {str(e)}')
        return render(request, 'panel/workspaces.html', {'tenants': [], 'products': []})


@login_required
@user_passes_test(is_superuser)
def create_workspace(request):
    """Crea un nuevo workspace"""
    if request.method == 'POST':
        try:
            company_name = request.POST.get('company_name')
            subdomain = request.POST.get('subdomain').lower()
            product_id = request.POST.get('product')
            plan = request.POST.get('plan', 'free')
            workspace_type = request.POST.get('type', 'shared')
            owner_username = request.POST.get('owner_username')
            create_github_repo = request.POST.get('create_github_repo') == 'on'
            
            # Auto-crear usuario predeterminado si no se especifica
            if not owner_username or owner_username == 'auto':
                owner_username = f"{subdomain}_admin"
            
            # Crear o obtener usuario owner
            owner, created = User.objects.get_or_create(
                username=owner_username,
                defaults={
                    'email': f'{owner_username}@{subdomain}.surgir.online',
                    'first_name': company_name,
                    'last_name': '(Predeterminado)',
                    'is_active': True,
                    'is_staff': False,
                    'is_superuser': False,
                }
            )
            
            if created:
                owner.set_password('admin123')  # Password predeterminado
                owner.save()
                messages.info(request, f'Usuario predeterminado creado: {owner_username} (password: admin123)')
            
            if Tenant.objects.filter(subdomain=subdomain).exists():
                messages.error(request, f'El subdominio {subdomain} ya existe')
                return redirect('create_workspace')
            
            product = Product.objects.get(id=product_id)
            
            # Si el usuario fue creado, agregarlo a la tabla master del producto
            if created:
                try:
                    create_product_user(
                        product.name,
                        None,  # tenant_id = None para owner
                        owner_username,
                        'admin123',
                        owner.email,
                        '',
                        'username'
                    )
                except Exception as e:
                    print(f"Error creando usuario en producto: {e}")
            
            # Sanitizar subdomain para nombres de BD (reemplazar guiones por guiones bajos)
            safe_subdomain = subdomain.replace('-', '_')
            db_name = f"tenant_{safe_subdomain}"
            db_user = f"user_{safe_subdomain}"
            db_password = generate_password()
            
            create_database(db_name, db_user, db_password)
            
            if workspace_type == 'dedicated':
                project_path = f"/opt/proyectos/{product.name}-system-clients/{subdomain}"
                stack_path = f"{project_path}/docker-compose.yml"
            else:
                project_path = product.template_path or f"/opt/proyectos/{product.name}-system"
                stack_path = ""
            
            tenant = Tenant.objects.create(
                name=company_name,
                subdomain=subdomain,
                company_name=company_name,
                product=product,
                plan=plan,
                type=workspace_type,
                status='active',
                db_name=db_name,
                db_user=db_user,
                db_password=db_password,
                project_path=project_path,
                stack_path=stack_path,
                git_repo_url='' if not create_github_repo else f'https://github.com/kritaar/{product.name}-{subdomain}',
                owner=owner,
                is_deployed=False
            )
            
            # Crear usuario admin en la tabla master del producto
            ensure_super_admin_in_product(product.name, request.user)
            
            # Si es SHARED y el checkbox está marcado, inicializar repo
            if workspace_type == 'shared' and create_github_repo:
                try:
                    # Verificar si ya existe el repo del producto
                    if not product.github_repo_url:
                        # Inicializar repo base del producto
                        repo_result = initialize_product_repo(product.name)
                        
                        if repo_result.get('success'):
                            # Actualizar producto con URL del repo
                            product.github_repo_url = repo_result.get('repo_url', '')
                            product.template_path = repo_result.get('path', '')
                            product.save()
                            
                            # Actualizar tenant con info del repo
                            tenant.git_repo_url = product.github_repo_url
                            tenant.save()
                            
                            messages.success(request, f'Repositorio base inicializado: {product.github_repo_url}')
                        else:
                            messages.warning(request, f'No se pudo inicializar repositorio: {repo_result.get("error")}')
                    else:
                        # Repo ya existe, solo asignar
                        tenant.git_repo_url = product.github_repo_url
                        tenant.save()
                        messages.info(request, f'Repositorio base ya existe: {product.github_repo_url}')
                except Exception as e:
                    messages.warning(request, f'No se pudo inicializar repositorio: {str(e)}')
            
            # Si es dedicado y el checkbox está marcado, ejecutar deployment automático
            if workspace_type == 'dedicated' and create_github_repo:
                try:
                    deploy_result = deploy_dedicated_workspace(
                        product.name,
                        subdomain,
                        db_name,
                        db_user,
                        db_password
                    )
                    
                    if deploy_result.get('success'):
                        tenant.git_repo_url = deploy_result.get('repo_url', '')
                        tenant.is_deployed = True
                        tenant.save()
                        messages.success(request, f'Workspace {company_name} desplegado exitosamente')
                    else:
                        messages.warning(request, f'Workspace creado pero deployment falló: {deploy_result.get("error")}')
                except Exception as e:
                    messages.warning(request, f'Workspace creado pero deployment falló: {str(e)}')
            
            ActivityLog.objects.create(
                tenant=tenant,
                user=request.user,
                action='create',
                description=f'Workspace {company_name} ({workspace_type}) creado',
                ip_address=get_client_ip(request)
            )
            
            messages.success(request, f'Workspace {company_name} creado exitosamente')
            return redirect('workspace_detail', tenant_id=tenant.id)
            
        except Exception as e:
            messages.error(request, f'Error al crear workspace: {str(e)}')
            return redirect('create_workspace')
    
    products = Product.objects.filter(is_active=True)
    users = User.objects.filter(is_active=True)
    
    context = {
        'products': products,
        'users': users,
    }
    return render(request, 'panel/create_workspace.html', context)


@login_required
@user_passes_test(is_superuser)
def edit_workspace(request, tenant_id):
    """Editar un workspace existente"""
    try:
        tenant = get_object_or_404(Tenant, id=tenant_id)
        
        if request.method == 'POST':
            tenant.company_name = request.POST.get('company_name')
            tenant.plan = request.POST.get('plan')
            tenant.max_users = int(request.POST.get('max_users', 5))
            tenant.storage_limit_gb = int(request.POST.get('storage_limit_gb', 10))
            
            new_owner_id = request.POST.get('owner_id')
            if new_owner_id:
                tenant.owner = User.objects.get(id=new_owner_id)
            
            tenant.save()
            
            ActivityLog.objects.create(
                tenant=tenant,
                user=request.user,
                action='update',
                description=f'Workspace {tenant.company_name} actualizado',
                ip_address=get_client_ip(request)
            )
            
            messages.success(request, f'Workspace {tenant.company_name} actualizado exitosamente')
            return redirect('workspace_detail', tenant_id=tenant.id)
        
        users = User.objects.filter(is_active=True)
        
        context = {
            'tenant': tenant,
            'users': users,
        }
        return render(request, 'panel/edit_workspace.html', context)
        
    except Exception as e:
        messages.error(request, f'Error al editar workspace: {str(e)}')
        return redirect('workspaces')


@login_required
@user_passes_test(is_superuser)
def workspace_detail(request, tenant_id):
    """Detalle de un workspace"""
    try:
        tenant = get_object_or_404(Tenant, id=tenant_id)
        tenant_users = TenantUser.objects.filter(tenant=tenant).select_related('user')
        activity = ActivityLog.objects.filter(tenant=tenant).order_by('-created_at')[:20]
        
        # Obtener usuarios del producto
        product_users = get_product_users(tenant.product.name, tenant.id)
        
        context = {
            'tenant': tenant,
            'tenant_users': tenant_users,
            'activity': activity,
            'product_users': product_users,
        }
        return render(request, 'panel/workspace_detail.html', context)
    except Exception as e:
        messages.error(request, f'Error al cargar workspace: {str(e)}')
        return redirect('workspaces')


@login_required
@user_passes_test(is_superuser)
def manage_workspace_users(request, tenant_id):
    """Gestionar usuarios de un workspace"""
    try:
        tenant = get_object_or_404(Tenant, id=tenant_id)
        product_name = tenant.product.name
        
        if request.method == 'POST':
            action = request.POST.get('action')
            
            if action == 'create':
                username = request.POST.get('username')
                password = request.POST.get('password')
                email = request.POST.get('email', '')
                phone = request.POST.get('phone', '')
                login_type = request.POST.get('login_type', 'username')
                
                create_product_user(product_name, tenant.id, username, password, email, phone, login_type)
                messages.success(request, f'Usuario {username} creado exitosamente')
                
            elif action == 'delete':
                user_id = request.POST.get('user_id')
                delete_product_user(product_name, user_id)
                messages.success(request, 'Usuario eliminado')
            
            return redirect('manage_workspace_users', tenant_id=tenant_id)
        
        # GET - Listar usuarios
        users = get_product_users(product_name, tenant.id)
        
        context = {
            'tenant': tenant,
            'users': users,
        }
        return render(request, 'panel/manage_users.html', context)
        
    except Exception as e:
        messages.error(request, f'Error: {str(e)}')
        return redirect('workspace_detail', tenant_id=tenant_id)


@login_required
@user_passes_test(is_superuser)
def create_workspace_repo(request, tenant_id):
    """Crea un repositorio GitHub para un workspace existente"""
    if request.method == 'POST':
        try:
            tenant = get_object_or_404(Tenant, id=tenant_id)
            
            # Verificar si ya tiene repo
            if tenant.git_repo_url:
                messages.warning(request, f'Este workspace ya tiene un repositorio: {tenant.git_repo_url}')
                return redirect('workspace_detail', tenant_id=tenant.id)
            
            # Crear repositorio según el tipo
            if tenant.type == 'shared':
                # Para SHARED, inicializar repo base del producto
                result = initialize_product_repo(tenant.product.name)
                
                if result.get('success'):
                    # Actualizar producto
                    tenant.product.github_repo_url = result.get('repo_url', '')
                    tenant.product.template_path = result.get('path', '')
                    tenant.product.save()
                    
                    # Actualizar tenant
                    tenant.git_repo_url = result.get('repo_url', '')
                    tenant.save()
                    
                    repo_url = result.get('repo_url', '')
                    if repo_url:
                        messages.success(request, f'Repositorio creado: {repo_url}')
                    else:
                        messages.success(request, 'Repositorio creado exitosamente')
                else:
                    messages.error(request, f'Error al crear repositorio: {result.get("error")}')
                    
            elif tenant.type == 'dedicated':
                # Para DEDICATED, hacer deployment completo
                result = deploy_dedicated_workspace(
                    tenant.product.name,
                    tenant.subdomain,
                    tenant.db_name,
                    tenant.db_user,
                    tenant.db_password
                )
                
                if result.get('success'):
                    tenant.git_repo_url = result.get('repo_url', '')
                    tenant.is_deployed = True
                    tenant.save()
                    
                    repo_url = result.get('repo_url', '')
                    if repo_url:
                        messages.success(request, f'Repositorio y deployment creados: {repo_url}')
                    else:
                        messages.success(request, 'Repositorio y deployment creados exitosamente')
                else:
                    messages.error(request, f'Error al crear repositorio: {result.get("error")}')
            
            # Log de actividad
            ActivityLog.objects.create(
                tenant=tenant,
                user=request.user,
                action='create',
                description=f'Repositorio GitHub creado para {tenant.company_name}',
                ip_address=get_client_ip(request)
            )
            
        except Exception as e:
            messages.error(request, f'Error al crear repositorio: {str(e)}')
        
        return redirect('workspace_detail', tenant_id=tenant_id)
    
    return redirect('workspaces')


@login_required
@user_passes_test(is_superuser)
def workspace_action(request, tenant_id):
    """Acciones sobre un workspace"""
    if request.method == 'POST':
        try:
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
                
            elif action == 'mark_inactive':
                tenant.status = 'inactive'
                tenant.save()
                messages.success(request, f'Workspace {tenant.company_name} marcado como inactivo')
                
            elif action == 'delete_permanent':
                # Eliminar PERMANENTEMENTE
                company_name = tenant.company_name
                db_name = tenant.db_name
                db_user = tenant.db_user
                project_path = tenant.project_path
                
                # 1. Eliminar usuarios del producto
                try:
                    delete_all_product_users(tenant.product.name, tenant.id)
                except Exception as e:
                    print(f"Error eliminando usuarios: {e}")
                
                # 2. Eliminar base de datos
                try:
                    delete_database(db_name, db_user)
                except Exception as e:
                    print(f"Error eliminando BD: {e}")
                
                # 3. Eliminar archivos del proyecto (solo dedicados)
                if tenant.type == 'dedicated' and project_path:
                    try:
                        if os.path.exists(project_path):
                            shutil.rmtree(project_path)
                    except Exception as e:
                        print(f"Error eliminando archivos: {e}")
                
                # 4. Eliminar el tenant de la BD
                tenant.delete()
                
                messages.success(request, f'Workspace {company_name} eliminado permanentemente')
                return redirect('workspaces')
                
            ActivityLog.objects.create(
                tenant=tenant,
                user=request.user,
                action=action,
                description=f'Acción {action} ejecutada en {tenant.company_name}',
                ip_address=get_client_ip(request)
            )
            
            return redirect('workspace_detail', tenant_id=tenant.id)
        except Exception as e:
            messages.error(request, f'Error al ejecutar acción: {str(e)}')
            return redirect('workspaces')
    
    return redirect('workspaces')


@login_required
@user_passes_test(is_superuser)
def clients(request):
    """Lista de clientes"""
    try:
        users = User.objects.annotate(
            tenant_count=Count('owned_tenants')
        ).order_by('-date_joined')
        
        context = {
            'users': users,
        }
        return render(request, 'panel/clients.html', context)
    except Exception as e:
        messages.error(request, f'Error al cargar clientes: {str(e)}')
        return render(request, 'panel/clients.html', {'users': []})


@login_required
@user_passes_test(is_superuser)
def deployments(request):
    """Lista de deployments"""
    try:
        dedicated_tenants = Tenant.objects.filter(type='dedicated').select_related('product', 'owner')
        shared_products = Product.objects.filter(is_active=True)
        
        context = {
            'dedicated_tenants': dedicated_tenants,
            'shared_products': shared_products,
        }
        return render(request, 'panel/deployments.html', context)
    except Exception as e:
        messages.error(request, f'Error al cargar deployments: {str(e)}')
        return render(request, 'panel/deployments.html', {})


@login_required
@user_passes_test(is_superuser)
def products(request):
    """Lista de productos"""
    try:
        all_products = Product.objects.annotate(
            tenant_count=Count('tenant')
        ).all()
        
        context = {
            'products': all_products,
        }
        return render(request, 'panel/products.html', context)
    except Exception as e:
        messages.error(request, f'Error al cargar productos: {str(e)}')
        return render(request, 'panel/products.html', {'products': []})


@login_required
@user_passes_test(is_superuser)
def databases(request):
    """Lista de bases de datos jerárquica"""
    try:
        # 1. Sistema Maestro
        master_db = {
            'name': 'tenant_master',
            'type': 'master',
            'users_count': User.objects.count(),
            'products_count': Product.objects.count(),
            'workspaces_count': Tenant.objects.count(),
        }
        
        # 2. Por Producto
        products = Product.objects.filter(is_active=True).annotate(
            tenant_count=Count('tenant')
        )
        
        products_data = []
        for product in products:
            # Workspaces SHARED
            shared_tenants = Tenant.objects.filter(
                product=product,
                type='shared'
            ).select_related('owner')
            
            shared_data = []
            for tenant in shared_tenants:
                # Contar usuarios del tenant
                user_count = len(get_product_users(product.name, tenant.id))
                
                # Contar tablas (intentar)
                table_count = get_table_count(tenant.db_name)
                
                shared_data.append({
                    'id': tenant.id,
                    'db_name': tenant.db_name,
                    'subdomain': tenant.subdomain,
                    'url': tenant.url,
                    'owner': tenant.owner.username,
                    'status': tenant.status,
                    'users_count': user_count,
                    'tables_count': table_count,
                    'created_at': tenant.created_at,
                })
            
            # Workspaces DEDICATED
            dedicated_tenants = Tenant.objects.filter(
                product=product,
                type='dedicated'
            ).select_related('owner')
            
            dedicated_data = []
            for tenant in dedicated_tenants:
                user_count = len(get_product_users(product.name, tenant.id))
                table_count = get_table_count(tenant.db_name)
                
                dedicated_data.append({
                    'id': tenant.id,
                    'db_name': tenant.db_name,
                    'subdomain': tenant.subdomain,
                    'url': tenant.url,
                    'owner': tenant.owner.username,
                    'status': tenant.status,
                    'users_count': user_count,
                    'tables_count': table_count,
                    'project_path': tenant.project_path,
                    'git_repo_url': tenant.git_repo_url,
                    'created_at': tenant.created_at,
                })
            
            products_data.append({
                'id': product.id,
                'name': product.name,
                'display_name': product.display_name,
                'icon': product.icon,
                'github_repo_url': product.github_repo_url,
                'template_path': product.template_path,
                'shared_count': len(shared_data),
                'dedicated_count': len(dedicated_data),
                'shared_tenants': shared_data,
                'dedicated_tenants': dedicated_data,
            })
        
        context = {
            'master_db': master_db,
            'products': products_data,
        }
        return render(request, 'panel/databases.html', context)
    except Exception as e:
        messages.error(request, f'Error al cargar bases de datos: {str(e)}')  
        return render(request, 'panel/databases.html', {'master_db': {}, 'products': []})


@login_required
@user_passes_test(is_superuser)
def database_manage(request, db_name):
    """Interfaz SQL para gestionar una base de datos específica"""
    try:
        # Verificar que la BD existe
        if db_name == 'tenant_master':
            db_info = {
                'name': db_name,
                'type': 'master',
                'workspace': None,
                'product_name': None,
            }
        else:
            tenant = Tenant.objects.filter(db_name=db_name).first()
            if not tenant:
                messages.error(request, f'Base de datos {db_name} no encontrada')
                return redirect('databases')
            
            db_info = {
                'name': db_name,
                'type': tenant.type,
                'workspace': tenant,
                'product_name': tenant.product.name,
            }
        
        # Si es POST, ejecutar query
        query_result = None
        if request.method == 'POST':
            sql_query = request.POST.get('sql_query', '').strip()
            
            if sql_query:
                query_result = execute_sql_query(db_name, sql_query)
        
        # Listar tablas
        tables = get_database_tables(db_name)
        
        context = {
            'db_info': db_info,
            'tables': tables,
            'query_result': query_result,
        }
        return render(request, 'panel/database_manage.html', context)
        
    except Exception as e:
        messages.error(request, f'Error: {str(e)}')
        return redirect('databases')


@login_required
@user_passes_test(is_superuser)
def database_users_api(request, db_name):
    """API para gestionar usuarios de un producto"""
    try:
        # Obtener nombre del producto
        if db_name == 'tenant_master':
            return JsonResponse({'error': 'No hay tabla de usuarios en tenant_master'}, status=400)
        
        tenant = Tenant.objects.filter(db_name=db_name).first()
        if not tenant:
            return JsonResponse({'error': 'Base de datos no encontrada'}, status=404)
        
        product_name = tenant.product.name
        table_name = f"{product_name}_users_master"
        
        # GET - Listar usuarios
        if request.method == 'GET':
            users = get_product_users(product_name, tenant.id)
            return JsonResponse({'users': users})
        
        # POST - Crear usuario
        elif request.method == 'POST':
            import json
            data = json.loads(request.body)
            
            username = data.get('username')
            password = data.get('password')
            email = data.get('email', '')
            phone = data.get('phone', '')
            login_type = data.get('login_type', 'username')
            
            create_product_user(product_name, tenant.id, username, password, email, phone, login_type)
            return JsonResponse({'success': True, 'message': f'Usuario {username} creado'})
        
        # PUT - Actualizar usuario
        elif request.method == 'PUT':
            import json
            data = json.loads(request.body)
            user_id = data.get('id')
            
            conn = psycopg2.connect(
                host=settings.DATABASES['default']['HOST'],
                port=settings.DATABASES['default']['PORT'],
                user=settings.DATABASES['default']['USER'],
                password=settings.DATABASES['default']['PASSWORD'],
                database='tenant_master'
            )
            cursor = conn.cursor()
            
            # Construir UPDATE
            updates = []
            params = []
            
            if 'email' in data:
                updates.append('email = %s')
                params.append(data['email'])
            if 'phone' in data:
                updates.append('phone = %s')
                params.append(data['phone'])
            if 'is_active' in data:
                updates.append('is_active = %s')
                params.append(data['is_active'])
            if 'password' in data and data['password']:
                updates.append('password = %s')
                params.append(make_password(data['password']))
            
            params.append(user_id)
            
            cursor.execute(f"""
                UPDATE {table_name}
                SET {', '.join(updates)}
                WHERE id = %s AND is_super_admin = FALSE
            """, params)
            
            conn.commit()
            cursor.close()
            conn.close()
            
            return JsonResponse({'success': True, 'message': 'Usuario actualizado'})
        
        # DELETE - Eliminar usuario
        elif request.method == 'DELETE':
            import json
            data = json.loads(request.body)
            user_id = data.get('id')
            
            delete_product_user(product_name, user_id)
            return JsonResponse({'success': True, 'message': 'Usuario eliminado'})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@user_passes_test(is_superuser)
def activity(request):
    """Log de actividades"""
    try:
        logs = ActivityLog.objects.select_related('user', 'tenant').order_by('-created_at')[:100]
        
        context = {
            'logs': logs,
        }
        return render(request, 'panel/activity.html', context)
    except Exception as e:
        messages.error(request, f'Error al cargar actividad: {str(e)}')
        return render(request, 'panel/activity.html', {'logs': []})


@login_required
@user_passes_test(is_superuser)
def settings_view(request):
    """Configuración del panel"""
    try:
        context = {
            'panel_domain': getattr(settings, 'PANEL_DOMAIN', 'panel.surgir.online'),
            'base_domain': getattr(settings, 'BASE_DOMAIN', 'surgir.online'),
        }
        return render(request, 'panel/settings.html', context)
    except Exception as e:
        messages.error(request, f'Error al cargar configuración: {str(e)}')
        return render(request, 'panel/settings.html', {})


# ============================================
# FUNCIONES AUXILIARES - USUARIOS DE PRODUCTOS
# ============================================

def get_product_users(product_name, tenant_id=None):
    """Obtiene usuarios de la tabla {product}_users_master"""
    try:
        with connection.cursor() as cursor:
            if tenant_id:
                cursor.execute(f"""
                    SELECT id, username, email, phone, login_type, is_super_admin, is_active, created_at
                    FROM {product_name}_users_master
                    WHERE tenant_id = %s OR is_super_admin = TRUE
                    ORDER BY is_super_admin DESC, created_at DESC
                """, [tenant_id])
            else:
                cursor.execute(f"""
                    SELECT id, username, email, phone, login_type, is_super_admin, is_active, created_at
                    FROM {product_name}_users_master
                    ORDER BY is_super_admin DESC, created_at DESC
                """)
            
            columns = [col[0] for col in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
    except Exception as e:
        print(f"Error getting product users: {e}")
        return []


def create_product_user(product_name, tenant_id, username, password, email='', phone='', login_type='username'):
    """Crea un usuario en la tabla {product}_users_master"""
    hashed_password = make_password(password)
    
    with connection.cursor() as cursor:
        cursor.execute(f"""
            INSERT INTO {product_name}_users_master 
            (tenant_id, username, password, email, phone, login_type, is_super_admin, is_active, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, FALSE, TRUE, NOW())
        """, [tenant_id, username, hashed_password, email, phone, login_type])


def delete_product_user(product_name, user_id):
    """Elimina un usuario de la tabla {product}_users_master"""
    with connection.cursor() as cursor:
        cursor.execute(f"""
            DELETE FROM {product_name}_users_master WHERE id = %s AND is_super_admin = FALSE
        """, [user_id])


def delete_all_product_users(product_name, tenant_id):
    """Elimina TODOS los usuarios de un tenant de la tabla master"""
    with connection.cursor() as cursor:
        cursor.execute(f"""
            DELETE FROM {product_name}_users_master 
            WHERE tenant_id = %s AND is_super_admin = FALSE
        """, [tenant_id])


def ensure_super_admin_in_product(product_name, admin_user):
    """Asegura que el super admin exista en la tabla del producto"""
    try:
        with connection.cursor() as cursor:
            # Verificar si ya existe
            cursor.execute(f"""
                SELECT id FROM {product_name}_users_master 
                WHERE username = %s AND is_super_admin = TRUE
            """, [admin_user.username])
            
            if not cursor.fetchone():
                # Crear super admin
                hashed_password = make_password('admin123')  # Contraseña default
                cursor.execute(f"""
                    INSERT INTO {product_name}_users_master 
                    (tenant_id, username, password, email, phone, login_type, is_super_admin, is_active, created_at)
                    VALUES (NULL, %s, %s, %s, '', 'username', TRUE, TRUE, NOW())
                """, [admin_user.username, hashed_password, admin_user.email])
    except Exception as e:
        print(f"Error ensuring super admin: {e}")


# ============================================
# FUNCIONES AUXILIARES - BASE DE DATOS
# ============================================

def create_database(db_name, db_user, db_password):
    """Crea una base de datos y usuario para el tenant"""
    try:
        conn = psycopg2.connect(
            host=settings.DATABASES['default']['HOST'],
            port=settings.DATABASES['default']['PORT'],
            user=settings.DATABASES['default']['USER'],
            password=settings.DATABASES['default']['PASSWORD'],
            database='postgres'
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        try:
            cursor.execute(f"SELECT 1 FROM pg_roles WHERE rolname = '{db_user}'")
            if not cursor.fetchone():
                cursor.execute(f"CREATE USER {db_user} WITH PASSWORD '{db_password}'")
            
            cursor.execute(f"SELECT 1 FROM pg_database WHERE datname = '{db_name}'")
            if not cursor.fetchone():
                cursor.execute(f"CREATE DATABASE {db_name} OWNER {db_user}")
            
            cursor.execute(f"GRANT ALL PRIVILEGES ON DATABASE {db_name} TO {db_user}")
            
        finally:
            cursor.close()
            conn.close()
    except Exception as e:
        raise Exception(f"Error al crear base de datos: {str(e)}")


def delete_database(db_name, db_user):
    """Elimina una base de datos y usuario del tenant"""
    try:
        conn = psycopg2.connect(
            host=settings.DATABASES['default']['HOST'],
            port=settings.DATABASES['default']['PORT'],
            user=settings.DATABASES['default']['USER'],
            password=settings.DATABASES['default']['PASSWORD'],
            database='postgres'
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        try:
            # Terminar conexiones activas a la BD
            cursor.execute(f"""
                SELECT pg_terminate_backend(pg_stat_activity.pid)
                FROM pg_stat_activity
                WHERE pg_stat_activity.datname = '{db_name}'
                AND pid <> pg_backend_pid()
            """)
            
            # Eliminar BD
            cursor.execute(f"DROP DATABASE IF EXISTS {db_name}")
            
            # Eliminar usuario
            cursor.execute(f"DROP USER IF EXISTS {db_user}")
            
        finally:
            cursor.close()
            conn.close()
    except Exception as e:
        raise Exception(f"Error al eliminar base de datos: {str(e)}")


def get_client_ip(request):
    """Obtiene la IP del cliente"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def get_table_count(db_name):
    """Cuenta las tablas en una base de datos"""
    try:
        conn = psycopg2.connect(
            host=settings.DATABASES['default']['HOST'],
            port=settings.DATABASES['default']['PORT'],
            user=settings.DATABASES['default']['USER'],
            password=settings.DATABASES['default']['PASSWORD'],
            database=db_name
        )
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT COUNT(*)
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            AND table_type = 'BASE TABLE'
        """)
        
        count = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        return count
    except:
        return 0


def get_database_tables(db_name):
    """Obtiene lista de tablas de una base de datos con info"""
    try:
        conn = psycopg2.connect(
            host=settings.DATABASES['default']['HOST'],
            port=settings.DATABASES['default']['PORT'],
            user=settings.DATABASES['default']['USER'],
            password=settings.DATABASES['default']['PASSWORD'],
            database=db_name
        )
        cursor = conn.cursor()
        
        # Obtener tablas con conteo de filas
        cursor.execute("""
            SELECT 
                schemaname,
                tablename,
                (SELECT COUNT(*) FROM information_schema.columns 
                 WHERE table_name = tablename) as column_count
            FROM pg_tables
            WHERE schemaname = 'public'
            ORDER BY tablename
        """)
        
        tables = []
        for row in cursor.fetchall():
            schema, table_name, column_count = row
            
            # Obtener conteo de filas (puede ser lento en tablas grandes)
            try:
                cursor.execute(f'SELECT COUNT(*) FROM {table_name}')
                row_count = cursor.fetchone()[0]
            except:
                row_count = 0
            
            tables.append({
                'name': table_name,
                'columns': column_count,
                'rows': row_count,
            })
        
        cursor.close()
        conn.close()
        return tables
    except Exception as e:
        print(f"Error getting tables: {e}")
        return []


def execute_sql_query(db_name, sql_query):
    """Ejecuta una query SQL y retorna resultados"""
    try:
        conn = psycopg2.connect(
            host=settings.DATABASES['default']['HOST'],
            port=settings.DATABASES['default']['PORT'],
            user=settings.DATABASES['default']['USER'],
            password=settings.DATABASES['default']['PASSWORD'],
            database=db_name
        )
        cursor = conn.cursor()
        
        # Ejecutar query
        cursor.execute(sql_query)
        
        # Si es SELECT, obtener resultados
        if sql_query.strip().upper().startswith('SELECT'):
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            
            result = {
                'success': True,
                'type': 'select',
                'columns': columns,
                'rows': rows,
                'row_count': len(rows),
            }
        else:
            # Para INSERT, UPDATE, DELETE, etc.
            conn.commit()
            result = {
                'success': True,
                'type': 'modify',
                'affected_rows': cursor.rowcount,
            }
        
        cursor.close()
        conn.close()
        return result
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
        }


# ============================================
# FUNCIONES AUXILIARES - DEPLOYMENT
# ============================================

def deploy_dedicated_workspace(product_name, subdomain, db_name, db_user, db_password):
    """Ejecuta el script de deployment automático para workspaces dedicados"""
    try:
        script_path = '/app/infra/scripts/deploy_dedicated_workspace.py'
        
        result = subprocess.run(
            ['python3', script_path, product_name, subdomain, db_name, db_user, db_password],
            capture_output=True,
            text=True,
            timeout=300  # 5 minutos timeout
        )
        
        # Extraer JSON del output
        output_lines = result.stdout.split('\n')
        json_start = False
        json_output = []
        
        for line in output_lines:
            if '=== RESULT ===' in line:
                json_start = True
                continue
            if json_start and line.strip():
                json_output.append(line)
        
        if json_output:
            return json.loads(''.join(json_output))
        else:
            return {
                'success': False,
                'error': 'No se pudo parsear el resultado del deployment'
            }
            
    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'error': 'Deployment timeout (>5 min)'
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def initialize_product_repo(product_name):
    """Inicializa repositorio base para productos SHARED"""
    try:
        script_path = '/app/infra/scripts/initialize_product_repo.py'
        
        result = subprocess.run(
            ['python3', script_path, product_name],
            capture_output=True,
            text=True,
            timeout=120  # 2 minutos timeout
        )
        
        # Extraer JSON del output
        output_lines = result.stdout.split('\n')
        json_start = False
        json_output = []
        
        for line in output_lines:
            if '=== RESULT ===' in line:
                json_start = True
                continue
            if json_start and line.strip():
                json_output.append(line)
        
        if json_output:
            return json.loads(''.join(json_output))
        else:
            return {
                'success': False,
                'error': 'No se pudo parsear el resultado'
            }
            
    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'error': 'Timeout al inicializar repositorio'
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }
