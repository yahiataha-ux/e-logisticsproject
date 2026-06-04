from django.db import models
from apps.authentication.models import User
from apps.client.models import Order
from apps.logistics_core.models import Warehouse

class Zone(models.Model):
    nom = models.CharField(max_length=100)
    ville = models.CharField(max_length=100)
    latitude_centre = models.FloatField()
    longitude_centre = models.FloatField()
    rayon_km = models.FloatField(default=15.0)
    couleur_hex = models.CharField(max_length=7, default='#3B82F6')
    actif = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.nom} ({self.ville})"

class Chauffeur(models.Model):
    STATUT_CHOICES = [
        ('disponible', 'Disponible'),
        ('en_livraison', 'En livraison'),
        ('pause', 'En pause'),
        ('hors_service', 'Hors service'),
    ]
    TYPE_VEHICULE = [
        ('moto', 'Moto'),
        ('voiture', 'Voiture'),
        ('camionnette', 'Camionnette'),
        ('camion', 'Camion'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    zone = models.ForeignKey(Zone, on_delete=models.SET_NULL, null=True)
    telephone = models.CharField(max_length=20)
    type_vehicule = models.CharField(max_length=20, choices=TYPE_VEHICULE)
    immatriculation = models.CharField(max_length=20)
    capacite_max_kg = models.FloatField(default=100.0)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='disponible')
    latitude_actuelle = models.FloatField(null=True, blank=True)
    longitude_actuelle = models.FloatField(null=True, blank=True)
    total_livraisons = models.IntegerField(default=0)
    total_co2_economise_kg = models.FloatField(default=0.0)
    note_moyenne = models.FloatField(default=5.0)
    date_inscription = models.DateTimeField(auto_now_add=True)
    photo = models.ImageField(upload_to='chauffeurs/', null=True, blank=True)
    
    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} - {self.zone.nom if self.zone else 'Sans zone'}"

class MissionLivraison(models.Model):
    STATUT_MISSION = [
        ('assignee', 'Assignée'),
        ('acceptee', 'Acceptée'),
        ('en_route_entrepot', 'En route vers entrepôt'),
        ('colis_pris', 'Colis récupéré'),
        ('en_livraison', 'En cours de livraison'),
        ('livree', 'Livrée'),
        ('echec', 'Échec livraison'),
    ]
    chauffeur = models.ForeignKey(Chauffeur, on_delete=models.SET_NULL, null=True)
    commande = models.OneToOneField('client.Order', on_delete=models.CASCADE)
    entrepot = models.ForeignKey('logistics_core.Warehouse', on_delete=models.SET_NULL, null=True)
    statut = models.CharField(max_length=30, choices=STATUT_MISSION, default='assignee')
    
    trajet_json = models.JSONField(null=True, blank=True)
    distance_km = models.FloatField(null=True, blank=True)
    co2_estime_kg = models.FloatField(null=True, blank=True)
    co2_mode_classique_kg = models.FloatField(null=True, blank=True)
    co2_economise_kg = models.FloatField(null=True, blank=True)
    
    date_assignation = models.DateTimeField(auto_now_add=True)
    date_acceptation = models.DateTimeField(null=True, blank=True)
    date_livraison_effective = models.DateTimeField(null=True, blank=True)
    
    note_client = models.IntegerField(null=True, blank=True)
    commentaire_client = models.TextField(blank=True)
    
    def __str__(self):
        return f"Mission {self.id} - Cmd {self.commande.id} - {self.statut}"

class TourneeJournaliere(models.Model):
    chauffeur = models.ForeignKey(Chauffeur, on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)
    missions = models.ManyToManyField(MissionLivraison)
    
    trajet_optimise_json = models.JSONField(null=True, blank=True)
    distance_totale_km = models.FloatField(default=0)
    co2_total_kg = models.FloatField(default=0)
    co2_economise_total_kg = models.FloatField(default=0)
    statut = models.CharField(max_length=20, default='planifiee')
    
    def __str__(self):
        return f"Tournée de {self.chauffeur} le {self.date}"
