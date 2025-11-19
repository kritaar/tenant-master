from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.conf import settings
from ..models import Tenant, Product, ActivityLog
from .serializers import TenantSerializer, ProductSerializer
import requests
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

class TenantListCreateView(generics.ListCreateAPIView):
    queryset = Tenant.objects.select_related('product', 'owner').all()
    serializer_class = TenantSerializer
    permission_classes = [IsAuthenticated]
    
    def perform_create(self, serializer):
        subdomain = serializer.validated_data['subdomain']
        db_name = f"tenant_{subdomain}"
        
        self.create_database(db_name)
        
        tenant = serializer.save(
            db_name=db_name,
            owner=self.request.user
        )
        
        ActivityLog.objects.create(
            tenant=tenant,
            user=self.request.user,
            action='create',
            description=f'Tenant {tenant.company_name} creado vía API'
        )
    
    def create_database(self, db_name):
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

class TenantDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Tenant.objects.select_related('product', 'owner').all()
    serializer_class = TenantSerializer
    permission_classes = [IsAuthenticated]

class ConvertTenantView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request, pk):
        try:
            tenant = Tenant.objects.get(pk=pk)
            
            if tenant.type == 'shared':
                tenant.type = 'dedicated'
                message = f'Tenant {tenant.company_name} convertido a dedicado'
            else:
                tenant.type = 'shared'
                message = f'Tenant {tenant.company_name} convertido a compartido'
            
            tenant.save()
            
            ActivityLog.objects.create(
                tenant=tenant,
                user=request.user,
                action='update',
                description=message
            )
            
            serializer = TenantSerializer(tenant)
            return Response({
                'message': message,
                'tenant': serializer.data
            })
            
        except Tenant.DoesNotExist:
            return Response(
                {'error': 'Tenant no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )

class ProductListView(generics.ListAPIView):
    queryset = Product.objects.filter(is_active=True)
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]

class SyncDeploymentsView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        if not settings.PORTAINER_BASE or not settings.PORTAINER_API_KEY:
            return Response(
                {'error': 'Portainer no configurado'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            url = f"{settings.PORTAINER_BASE}/api/stacks"
            headers = {'X-API-Key': settings.PORTAINER_API_KEY}
            
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                stacks = response.json()
                return Response({
                    'message': f'{len(stacks)} stacks sincronizados',
                    'stacks': stacks
                })
            else:
                return Response(
                    {'error': 'Error al conectar con Portainer'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
                
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class GitHubWebhookView(APIView):
    """Recibe webhooks de GitHub para auto-deployment"""
    permission_classes = []  # Público, validamos con secret
    
    def post(self, request, product_name):
        import hmac
        import hashlib
        import subprocess
        import docker
        from ..models import ActivityLog
        
        # 1. Validar signature de GitHub
        signature = request.headers.get('X-Hub-Signature-256', '')
        secret = settings.GITHUB_WEBHOOK_SECRET.encode()
        
        expected_signature = 'sha256=' + hmac.new(
            secret,
            request.body,
            hashlib.sha256
        ).hexdigest()
        
        if not hmac.compare_digest(signature, expected_signature):
            return Response({'error': 'Invalid signature'}, status=403)
        
        # 2. Obtener info del push
        data = request.data
        ref = data.get('ref', '')
        
        # Solo procesar push a main/master
        if ref not in ['refs/heads/main', 'refs/heads/master']:
            return Response({'message': 'Branch ignored'}, status=200)
        
        # 3. Path del proyecto
        project_path = f"/opt/proyectos/{product_name}-system"
        
        try:
            # 4. Git pull
            result_pull = subprocess.run(
                ['git', 'pull', 'origin', 'main'],
                cwd=project_path,
                check=True,
                capture_output=True,
                text=True
            )
            
            # 5. Restart contenedor usando Docker API
            container_name = f"tenant-master-{product_name}-shared"
            
            try:
                client = docker.from_env()
                container = client.containers.get(container_name)
                container.restart()
                docker_output = f"Container {container_name} restarted successfully"
            except docker.errors.NotFound:
                docker_output = f"Warning: Container {container_name} not found (may not exist yet)"
            except Exception as docker_err:
                docker_output = f"Docker restart failed: {str(docker_err)}"
            
            # 6. Log de actividad
            ActivityLog.objects.create(
                user=None,
                action='auto-deploy',
                description=f'Auto-deployment ejecutado para {product_name}',
                ip_address=request.META.get('REMOTE_ADDR')
            )
            
            return Response({
                'success': True,
                'message': f'Deployment de {product_name} completado',
                'project_path': project_path,
                'container': container_name,
                'git_output': result_pull.stdout,
                'docker_output': docker_output
            })
            
        except subprocess.CalledProcessError as e:
            return Response({
                'success': False,
                'error': str(e),
                'stderr': e.stderr if hasattr(e, 'stderr') else ''
            }, status=500)
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=500)
