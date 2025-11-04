from rest_framework import serializers
from ..models import Tenant, Product
from django.contrib.auth.models import User

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'name', 'display_name', 'description', 'icon', 'is_active']

class TenantSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.display_name', read_only=True)
    owner_username = serializers.CharField(source='owner.username', read_only=True)
    url = serializers.URLField(read_only=True)
    
    class Meta:
        model = Tenant
        fields = [
            'id', 'name', 'subdomain', 'company_name', 
            'product', 'product_name', 'plan', 'type', 'status',
            'db_name', 'owner', 'owner_username', 'url',
            'max_users', 'storage_limit_gb',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['db_name', 'created_at', 'updated_at', 'url']
