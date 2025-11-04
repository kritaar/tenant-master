from django.conf import settings
from .models import Tenant

class TenantMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        host = request.get_host().split(':')[0]
        
        request.tenant = None
        
        if host != settings.PANEL_DOMAIN and not host.startswith('127.0.0.1') and not host.startswith('localhost'):
            subdomain = host.replace(f".{settings.BASE_DOMAIN}", "")
            
            try:
                tenant = Tenant.objects.get(subdomain=subdomain, status='active')
                request.tenant = tenant
            except Tenant.DoesNotExist:
                pass
        
        response = self.get_response(request)
        return response
