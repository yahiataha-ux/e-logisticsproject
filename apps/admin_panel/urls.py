from django.urls import path
from apps.admin_panel import views
from apps.admin_panel import views_chauffeurs

from django.shortcuts import redirect

urlpatterns = [
    path('', lambda request: redirect('admin_panel:dashboard')),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('users/', views.admin_users, name='users'),
    path('users/add/', views.admin_add_user, name='add_user'),
    path('export/csv/<str:model_type>/', views.export_data_csv, name='export_data_csv'),
    path('users/login-as/<int:user_id>/', views.admin_login_as, name='login_as'),
    path('users/logout-as/', views.admin_logout_as, name='logout_as'),
    path('users/edit/<int:user_id>/', views.admin_edit_user, name='edit_user'),
    path('users/delete/<int:user_id>/', views.admin_delete_user, name='delete_user'),
    path('companies/', views.admin_companies, name='companies'),
    path('companies/<int:company_id>/', views.admin_company_detail, name='company_detail'),
    path('transporters/', views.admin_transporters, name='transporters'),
    path('chauffeurs/', views_chauffeurs.liste_chauffeurs, name='chauffeurs'),
    path('chauffeurs/ajouter/', views_chauffeurs.ajouter_chauffeur, name='ajouter_chauffeur'),
    path('chauffeurs/modifier/<int:id>/', views_chauffeurs.modifier_chauffeur, name='modifier_chauffeur'),
    path('chauffeurs/supprimer/<int:id>/', views_chauffeurs.supprimer_chauffeur, name='supprimer_chauffeur'),
    path('chauffeurs/stats/<int:id>/', views_chauffeurs.stats_chauffeur, name='stats_chauffeur'),
    path('zones/', views_chauffeurs.gestion_zones, name='zones'),
    path('zones/ajouter/', views_chauffeurs.ajouter_zone, name='ajouter_zone'),
    path('missions/', views_chauffeurs.vue_missions, name='missions'),
    path('missions/assigner/', views_chauffeurs.assigner_missions, name='assigner_missions'),
    path('hubs/', views.admin_hubs, name='hubs'),
    path('warehouse/', views.admin_warehouse, name='warehouse'),
    path('flux/', views.admin_flux, name='flux'),
    path('orders/', views.admin_orders, name='orders'),
    path('orders/assign/', views.admin_assign_transporter, name='assign_transporter'),
    path('orders/<int:order_id>/', views.admin_order_detail, name='order_detail'),
    path('monitoring/', views.admin_monitoring, name='monitoring'),
    path('analytics/', views.admin_analytics, name='analytics'),
    path('settings/', views.admin_settings, name='settings'),
]
