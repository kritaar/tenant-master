from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Product(models.Model):
    """Productos disponibles (ERP, Inventario, Tienda, etc.)"""
    name = models.CharField(max_length=100, unique=True)
    display_name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=10, default='📦')
    
    # Path del template
    template_path = models.CharField(
        max_length=255,
        help_text="Path relativo desde /infra/deployments/. Ej: TEMPLATE_ERP"
    )
    
    # Imágenes Docker
    backend_image = models.CharField(max_length=200, blank=True)
    frontend_image = models.CharField(max_length=200, blank=True)
    
    # Características
    requires_database = models.BooleanField(default=True)
    supports_shared = models.BooleanField(default=True)
    supports_dedicated = models.BooleanField(default=True)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'panel_product'
        ordering = ['display_name']
    
    def __str__(self):
        return self.display_name


class Deployment(models.Model):
    """
    Instancia física de un producto
    - SHARED: Un deployment sirve a múltiples tenants
    - DEDICATED: Un deployment por tenant
    """
    TYPE_CHOICES = [
        ('SHARED', 'Compartido'),
        ('DEDICATED', 'Dedicado'),
    ]
    
    STATUS_CHOICES = [
        ('DEPLOYING', 'Desplegando'),
        ('ACTIVE', 'Activo'),
        ('ERROR', 'Error'),
        ('STOPPED', 'Detenido'),
    ]
    
    name = models.CharField(max_length=100, unique=True)
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='deployments')
    deployment_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DEPLOYING')
    
    # Path físico del deployment
    physical_path = models.CharField(
        max_length=255,
        help_text="Path absoluto en el servidor. Ej: /var/deployments/erp-shared"
    )
    
    # Docker Compose
    docker_compose_content = models.TextField(
        help_text="Contenido del docker-compose.yml usado"
    )
    
    # Portainer
    portainer_stack_id = models.IntegerField(null=True, blank=True)
    portainer_stack_name = models.CharField(max_length=100, blank=True)
    
    # Para deployments SHARED
    max_tenants = models.IntegerField(
        null=True,
        blank=True,
        help_text="Máximo de tenants (solo para SHARED)"
    )
    current_tenants = models.IntegerField(default=0)
    
    # Metadata
    error_message = models.TextField(blank=True)
    deployed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'panel_deployment'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.get_deployment_type_display()})"
    
    @property
    def is_available(self):
        """Verifica si el deployment puede aceptar más tenants"""
        if self.deployment_type == 'DEDICATED':
            return self.current_tenants == 0
        return self.max_tenants is None or self.current_tenants < self.max_tenants


class Tenant(models.Model):
    """Workspace/Cliente"""
    STATUS_CHOICES = [
        ('ACTIVE', 'Activo'),
        ('SUSPENDED', 'Suspendido'),
        ('INACTIVE', 'Inactivo'),
    ]
    
    PLAN_CHOICES = [
        ('free', 'Gratuito'),
        ('starter', 'Starter'),
        ('professional', 'Profesional'),
        ('enterprise', 'Enterprise'),
    ]
    
    name = models.CharField(max_length=100)
    subdomain = models.CharField(max_length=100, unique=True)
    company_name = models.CharField(max_length=200)
    
    # Producto y deployment
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    deployment = models.ForeignKey(
        Deployment,
        on_delete=models.PROTECT,
        related_name='tenants'
    )
    
    plan = models.CharField(max_length=20, choices=PLAN_CHOICES, default='free')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')
    
    # Database
    schema_name = models.CharField(max_length=100, unique=True)
    db_name = models.CharField(max_length=100)
    db_user = models.CharField(max_length=100)
    db_password = models.CharField(max_length=100)
    db_host = models.CharField(max_length=200, default='postgres')
    db_port = models.IntegerField(default=5432)
    
    # Owner
    owner = models.ForeignKey(User, on_delete=models.PROTECT, related_name='owned_tenants')
    
    # Limits
    max_users = models.IntegerField(default=5)
    storage_limit_gb = models.IntegerField(default=10)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'panel_tenant'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.company_name} ({self.subdomain})"
    
    @property
    def url(self):
        from django.conf import settings
        return f"https://{self.subdomain}.{settings.BASE_DOMAIN}"
    
    @property
    def database_url(self):
        return f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"


class TenantUser(models.Model):
    ROLE_CHOICES = [
        ('owner', 'Propietario'),
        ('admin', 'Administrador'),
        ('user', 'Usuario'),
    ]
    
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='users')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tenant_memberships')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='user')
    is_active = models.BooleanField(default=True)
    joined_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'panel_tenant_user'
        unique_together = ['tenant', 'user']
    
    def __str__(self):
        return f"{self.user.username} - {self.tenant.name} ({self.role})"


class ActivityLog(models.Model):
    ACTION_CHOICES = [
        ('create', 'Creación'),
        ('update', 'Actualización'),
        ('delete', 'Eliminación'),
        ('suspend', 'Suspensión'),
        ('activate', 'Activación'),
        ('login', 'Inicio de sesión'),
        ('deploy', 'Despliegue'),
    ]
    
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, null=True, blank=True)
    deployment = models.ForeignKey(Deployment, on_delete=models.CASCADE, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    description = models.TextField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'panel_activity_log'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.action} - {self.created_at}"
