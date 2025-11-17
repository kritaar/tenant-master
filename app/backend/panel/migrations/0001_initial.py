import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
                ('display_name', models.CharField(max_length=200)),
                ('description', models.TextField(blank=True)),
                ('icon', models.CharField(default='📦', max_length=10)),
                ('docker_image', models.CharField(blank=True, max_length=200)),
                ('template_path', models.CharField(blank=True, help_text='Path en /opt/proyectos/', max_length=255)),
                ('github_repo_url', models.CharField(blank=True, help_text='URL del repositorio GitHub del código base', max_length=500)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'db_table': 'panel_product',
                'ordering': ['display_name'],
            },
        ),
        migrations.CreateModel(
            name='Tenant',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('subdomain', models.CharField(max_length=100, unique=True)),
                ('company_name', models.CharField(max_length=200)),
                ('plan', models.CharField(choices=[('free', 'Gratuito'), ('starter', 'Starter'), ('professional', 'Profesional'), ('enterprise', 'Enterprise')], default='free', max_length=20)),
                ('type', models.CharField(choices=[('shared', 'Compartido'), ('dedicated', 'Dedicado')], default='dedicated', max_length=20)),
                ('status', models.CharField(choices=[('active', 'Activo'), ('suspended', 'Suspendido'), ('inactive', 'Inactivo')], default='active', max_length=20)),
                ('db_name', models.CharField(max_length=100, unique=True)),
                ('db_user', models.CharField(blank=True, max_length=100)),
                ('db_password', models.CharField(blank=True, max_length=255)),
                ('db_host', models.CharField(default='postgres', max_length=200)),
                ('db_port', models.IntegerField(default=5432)),
                ('project_path', models.CharField(blank=True, max_length=500)),
                ('stack_path', models.CharField(blank=True, max_length=500)),
                ('git_repo_url', models.CharField(blank=True, max_length=500)),
                ('stack_name', models.CharField(blank=True, max_length=100)),
                ('portainer_stack_id', models.IntegerField(blank=True, null=True)),
                ('max_users', models.IntegerField(default=5)),
                ('storage_limit_gb', models.IntegerField(default=10)),
                ('is_deployed', models.BooleanField(default=False)),
                ('deployed_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='owned_tenants', to=settings.AUTH_USER_MODEL)),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='panel.product')),
            ],
            options={
                'db_table': 'panel_tenant',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='ActivityLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action', models.CharField(choices=[('create', 'Creación'), ('update', 'Actualización'), ('delete', 'Eliminación'), ('suspend', 'Suspensión'), ('activate', 'Activación'), ('login', 'Inicio de sesión'), ('deploy', 'Despliegue')], max_length=20)),
                ('description', models.TextField()),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('tenant', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='panel.tenant')),
            ],
            options={
                'db_table': 'panel_activity_log',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='TenantUser',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role', models.CharField(choices=[('owner', 'Propietario'), ('admin', 'Administrador'), ('user', 'Usuario')], default='user', max_length=20)),
                ('is_active', models.BooleanField(default=True)),
                ('joined_at', models.DateTimeField(auto_now_add=True)),
                ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='users', to='panel.tenant')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tenant_memberships', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'panel_tenant_user',
                'unique_together': {('tenant', 'user')},
            },
        ),
    ]
