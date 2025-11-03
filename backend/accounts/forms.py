from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Workspace, Product
import re


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True, label="Email")
    first_name = forms.CharField(max_length=30, required=True, label="Nombre")
    company_name = forms.CharField(max_length=200, required=True, label="Nombre de la empresa")
    subdomain = forms.SlugField(
        max_length=100,
        required=True,
        label="Subdominio",
        help_text="Solo letras minúsculas, números y guiones. Ej: mi-empresa"
    )
    product = forms.ModelChoiceField(
        queryset=Product.objects.filter(is_active=True),
        required=True,
        label="Selecciona el producto",
        empty_label="-- Selecciona un producto --"
    )
    
    class Meta:
        model = User
        fields = ['first_name', 'email', 'username', 'password1', 'password2']
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Este email ya está registrado")
        return email
    
    def clean_subdomain(self):
        subdomain = self.cleaned_data.get('subdomain').lower()
        
        # Validar formato
        if not re.match(r'^[a-z0-9-]+$', subdomain):
            raise forms.ValidationError("Solo letras minúsculas, números y guiones")
        
        # Verificar longitud mínima
        if len(subdomain) < 3:
            raise forms.ValidationError("El subdominio debe tener al menos 3 caracteres")
        
        # Palabras reservadas
        reserved = ['www', 'app', 'api', 'admin', 'mail', 'ftp', 'smtp', 'pop', 'imap', 
                   'localhost', 'test', 'dev', 'staging', 'prod', 'demo']
        if subdomain in reserved:
            raise forms.ValidationError("Este nombre está reservado")
        
        # Verificar disponibilidad con el producto seleccionado
        product = self.cleaned_data.get('product')
        if product and Workspace.objects.filter(subdomain=subdomain, product=product).exists():
            raise forms.ValidationError("Este subdominio ya está ocupado para este producto")
        
        return subdomain
