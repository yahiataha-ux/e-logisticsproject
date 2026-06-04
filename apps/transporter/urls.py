from django.urls import path
from apps.transporter import views

urlpatterns = [
    path('', views.dashboard_chauffeur, name='dashboard'),
    path('mission/<int:id>/', views.mission_detail, name='mission_detail'),
    path('mission/<int:id>/livrer/', views.marquer_livre, name='marquer_livre'),
    path('mission/<int:id>/probleme/', views.signaler_probleme, name='signaler_probleme'),
    path('historique/', views.historique_chauffeur, name='historique'),
    path('notifications/', views.notifications_chauffeur, name='notifications'),
    path('statut/', views.changer_statut, name='changer_statut'),
    
    # API JSON pour la carte temps réel
    path('api/chauffeurs/positions/', views.api_positions_chauffeurs, name='api_positions'),
    path('api/missions/statut/<int:id>/', views.api_statut_mission, name='api_statut'),
]
