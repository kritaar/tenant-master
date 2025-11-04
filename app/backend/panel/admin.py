from django.contrib import admin
from .models import Product, Tenant, TenantUser, ActivityLog

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['display_name', 'name', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['name', 'display_name']

@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ['company_name', 'subdomain', 'product', 'plan', 'type', 'status', 'created_at']
    list_filter = ['type', 'status', 'plan', 'product']
    search_fields = ['name', 'company_name', 'subdomain']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(TenantUser)
class TenantUserAdmin(admin.ModelAdmin):
    list_display = ['user', 'tenant', 'role', 'is_active', 'joined_at']
    list_filter = ['role', 'is_active']
    search_fields = ['user__username', 'tenant__name']

@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ['action', 'user', 'tenant', 'created_at']
    list_filter = ['action', 'created_at']
    search_fields = ['description']
    readonly_fields = ['created_at']
