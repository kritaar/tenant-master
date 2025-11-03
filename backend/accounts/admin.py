from django.contrib import admin
from .models import Product, Workspace, WorkspaceMembership


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'display_name', 'subdomain_prefix', 'container_port', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'display_name']


@admin.register(Workspace)
class WorkspaceAdmin(admin.ModelAdmin):
    list_display = ['company_name', 'subdomain', 'product', 'is_active', 'created_at']
    list_filter = ['is_active', 'product', 'created_at']
    search_fields = ['company_name', 'subdomain']
    readonly_fields = ['created_at', 'updated_at', 'db_name', 'db_user', 'db_password']
    
    fieldsets = (
        ('Información del Workspace', {
            'fields': ('company_name', 'subdomain', 'product', 'is_active')
        }),
        ('Configuración de Base de Datos', {
            'fields': ('db_name', 'db_user', 'db_password', 'db_host', 'db_port'),
            'classes': ('collapse',)
        }),
        ('Fechas', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(WorkspaceMembership)
class WorkspaceMembershipAdmin(admin.ModelAdmin):
    list_display = ['user', 'workspace', 'role', 'joined_at']
    list_filter = ['role', 'joined_at']
    search_fields = ['user__username', 'workspace__company_name']
