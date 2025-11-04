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
