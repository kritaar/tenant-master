"""
Modelos para gestión de workspaces multi-tenant
"""
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
import secrets
import string


def generate_password(length=24):
    """Genera contraseña segura para BD"""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for _ in range(length))


class Product(models.Model):
    """Productos disponibles (Inventario, ERP, Shop, etc)"""
    name = models.CharField(max_length=100, unique=True)
    display_name = models.CharField(max_length=200)
    subdomain_prefix = models.CharField(max_length=50, help_text="Ej: inv, erp, shop")
    container_port = models.IntegerField(help_text="Puerto del contenedor Docker")
    version = models.CharField(max_length=20, default="1.0.0")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Producto"
        verbose_name_plural = "Productos"
        ordering = ['name']
    
    def __str__(self):
        return self.display_name


class Workspace(models.Model):
    """Espacio de trabajo = Tenant = Cliente"""
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    company_name = models.CharField(max_length=200, verbose_name="Nombre de la empresa")
    subdomain = models.SlugField(
        max_length=100,
        validators=[
            RegexValidator(
                regex='^[a-z0-9-]+$',
                message='Solo letras minúsculas, números y guiones'
            )
        ],
        verbose_name="Subdominio"
    )
    
    # Configuración de base de datos
    db_name = models.CharField(max_length=100, unique=True)
    db_user = models.CharField(max_length=100)
    db_password = models.CharField(max_length=200)
    db_host = models.CharField(max_length=100, default='postgres16')
    db_port = models.IntegerField(default=5432)
    
    # Estado
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Workspace"
        verbose_name_plural = "Workspaces"
        ordering = ['-created_at']
        unique_together = ['product', 'subdomain']
    
    def __str__(self):
        return f"{self.company_name} ({self.subdomain}.{self.product.subdomain_prefix})"
    
    @property
    def url(self):
        """URL completa del workspace"""
        from django.conf import settings
        domain = settings.TENANT_DOMAIN
        return f"https://{self.subdomain}.{self.product.subdomain_prefix}.{domain}"


class WorkspaceMembership(models.Model):
    """Membresía de usuario en un workspace"""
    
    ROLE_CHOICES = [
        ('owner', 'Propietario'),
        ('admin', 'Administrador'),
        ('member', 'Miembro'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='member')
    joined_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'workspace']
        verbose_name = "Membresía"
        verbose_name_plural = "Membresías"
    
    def __str__(self):
        return f"{self.user.username} - {self.workspace.company_name} ({self.role})"
