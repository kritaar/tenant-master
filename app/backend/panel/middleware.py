"""
Middleware Multi-Tenant para routing de subdominios
"""
from django.shortcuts import render
from django.http import HttpResponse
from .models import Tenant


class TenantMiddleware:
    """
    Middleware que detecta el subdomain y carga el tenant correspondiente
    """
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Obtener host sin puerto
        host = request.get_host().split(':')[0]
        
        # Extraer subdomain (primer segmento antes del dominio base)
        parts = host.split('.')
        
        # Si es el panel principal (panel.surgir.online), dejar pasar
        if parts[0] == 'panel' or len(parts) < 3:
            request.tenant = None
            return self.get_response(request)
        
        # Extraer subdomain (ej: autominirep de autominirep.surgir.online)
        subdomain = parts[0]
        
        # Buscar tenant por subdomain
        try:
            tenant = Tenant.objects.get(subdomain=subdomain, status='active')
            request.tenant = tenant
            
            # Si el tenant no está deployed, mostrar página de "en construcción"
            if not tenant.is_deployed:
                return HttpResponse(f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <title>{tenant.company_name} - En Construcción</title>
                    <style>
                        body {{
                            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                            display: flex;
                            align-items: center;
                            justify-content: center;
                            min-height: 100vh;
                            margin: 0;
                            color: white;
                        }}
                        .container {{
                            text-align: center;
                            padding: 2rem;
                        }}
                        h1 {{
                            font-size: 3rem;
                            margin-bottom: 1rem;
                        }}
                        p {{
                            font-size: 1.2rem;
                            opacity: 0.9;
                        }}
                        .icon {{
                            font-size: 5rem;
                            margin-bottom: 1rem;
                        }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="icon">{tenant.product.icon}</div>
                        <h1>{tenant.company_name}</h1>
                        <p>🚧 Sistema en construcción</p>
                        <p>Workspace: {tenant.subdomain}.surgir.online</p>
                        <p>Producto: {tenant.product.display_name}</p>
                    </div>
                </body>
                </html>
                """, content_type='text/html')
            
            # TODO: Aquí eventualmente redirigirás a la aplicación del producto
            # Por ahora, mostrar info del workspace
            return HttpResponse(f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>{tenant.company_name}</title>
                <style>
                    body {{
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        min-height: 100vh;
                        margin: 0;
                        color: white;
                    }}
                    .container {{
                        text-align: center;
                        padding: 2rem;
                        background: rgba(255, 255, 255, 0.1);
                        border-radius: 1rem;
                        backdrop-filter: blur(10px);
                    }}
                    h1 {{
                        font-size: 2.5rem;
                        margin-bottom: 1rem;
                    }}
                    .info {{
                        text-align: left;
                        margin-top: 2rem;
                        padding: 1rem;
                        background: rgba(0, 0, 0, 0.2);
                        border-radius: 0.5rem;
                    }}
                    .info p {{
                        margin: 0.5rem 0;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>{tenant.product.icon} {tenant.company_name}</h1>
                    <p>✅ Workspace activo y configurado</p>
                    <div class="info">
                        <p><strong>Subdomain:</strong> {tenant.subdomain}</p>
                        <p><strong>Producto:</strong> {tenant.product.display_name}</p>
                        <p><strong>Plan:</strong> {tenant.get_plan_display()}</p>
                        <p><strong>Tipo:</strong> {tenant.get_type_display()}</p>
                        <p><strong>Base de datos:</strong> {tenant.db_name}</p>
                        <p><strong>URL completa:</strong> {tenant.url}</p>
                    </div>
                    <p style="margin-top: 2rem; opacity: 0.7;">
                        💡 Pronto se cargará la aplicación {tenant.product.display_name}
                    </p>
                </div>
            </body>
            </html>
            """, content_type='text/html')
            
        except Tenant.DoesNotExist:
            # Subdomain no existe
            return HttpResponse(f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Workspace no encontrado</title>
                <style>
                    body {{
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        min-height: 100vh;
                        margin: 0;
                        color: white;
                    }}
                    .container {{
                        text-align: center;
                        padding: 2rem;
                    }}
                    h1 {{
                        font-size: 3rem;
                        margin-bottom: 1rem;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>❌ 404</h1>
                    <p>El workspace "{subdomain}" no existe</p>
                    <p><a href="https://panel.surgir.online" style="color: white;">← Volver al panel</a></p>
                </div>
            </body>
            </html>
            """, content_type='text/html', status=404)
