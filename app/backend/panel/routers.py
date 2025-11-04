from django.conf import settings

class TenantRouter:
    def db_for_read(self, model, **hints):
        if model._meta.app_label == 'panel':
            return 'default'
        
        request = hints.get('request')
        if request and hasattr(request, 'tenant') and request.tenant:
            return request.tenant.db_name
        
        return 'default'
    
    def db_for_write(self, model, **hints):
        if model._meta.app_label == 'panel':
            return 'default'
        
        request = hints.get('request')
        if request and hasattr(request, 'tenant') and request.tenant:
            return request.tenant.db_name
        
        return 'default'
    
    def allow_relation(self, obj1, obj2, **hints):
        return True
    
    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label == 'panel':
            return db == 'default'
        
        return True
