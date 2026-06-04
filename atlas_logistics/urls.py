from django.contrib import admin
from django.urls import path, include
from apps.authentication import views as views
from django.shortcuts import redirect

def home_redirect(request):
    if not request.user.is_authenticated:
        return redirect('login')
    
    role = request.user.role
    if role == 'Admin':
        return redirect('admin_panel:dashboard')
    elif role == 'Entreprise':
        return redirect('enterprise:dashboard')
    elif role == 'Transporteur':
        return redirect('transporter:dashboard')
    elif role == 'Client':
        return redirect('client:marketplace')
    
    return redirect('login')

urlpatterns = [
    path('django-admin/', admin.site.urls), # Renamed to avoid conflict with my admin_panel
    path('', home_redirect, name='home'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.custom_logout, name='logout'),
    path('admin/', include(('apps.admin_panel.urls', 'admin_panel'), namespace='admin_panel')),
    path('enterprise/', include(('apps.enterprise.urls', 'enterprise'), namespace='enterprise')),
    path('transporter/', include(('apps.transporter.urls', 'transporter'), namespace='transporter')),
    path('client/', include(('apps.client.urls', 'client'), namespace='client')),
]
