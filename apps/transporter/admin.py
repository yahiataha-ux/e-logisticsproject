from django.contrib import admin
from .models import Zone, Chauffeur, MissionLivraison

@admin.register(Zone)
class ZoneAdmin(admin.ModelAdmin):
    list_display = ('nom', 'ville', 'actif')

@admin.register(Chauffeur)
class ChauffeurAdmin(admin.ModelAdmin):
    list_display = ('user', 'zone', 'type_vehicule', 'statut')
    list_filter = ('statut', 'type_vehicule', 'zone')

@admin.register(MissionLivraison)
class MissionLivraisonAdmin(admin.ModelAdmin):
    list_display = ('id', 'chauffeur', 'commande', 'statut')
    list_filter = ('statut',)
