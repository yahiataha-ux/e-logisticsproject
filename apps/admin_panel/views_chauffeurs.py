import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import get_user_model
from apps.transporter.models import Chauffeur, Zone, MissionLivraison
from apps.client.models import Order
from apps.transporter.algorithms.dijkstra_tournee import dijkstra, graphe, noeuds
from django.db.models import Sum
from django.utils import timezone

User = get_user_model()

def is_admin(user):
    return user.is_authenticated and user.role == 'Admin'

@login_required
@user_passes_test(is_admin)
def liste_chauffeurs(request):
    chauffeurs = Chauffeur.objects.all().select_related('user', 'zone')
    
    # Filtres
    zone_id = request.GET.get('zone')
    statut = request.GET.get('statut')
    vehicule = request.GET.get('vehicule')
    
    if zone_id:
        chauffeurs = chauffeurs.filter(zone_id=zone_id)
    if statut:
        chauffeurs = chauffeurs.filter(statut=statut)
    if vehicule:
        chauffeurs = chauffeurs.filter(type_vehicule=vehicule)
        
    zones = Zone.objects.all()
    
    # Stats
    total_chauffeurs = chauffeurs.count()
    disponibles = chauffeurs.filter(statut='disponible').count()
    en_livraison = chauffeurs.filter(statut='en_livraison').count()
    co2_total_economise = chauffeurs.aggregate(Sum('total_co2_economise_kg'))['total_co2_economise_kg__sum'] or 0

    context = {
        'chauffeurs': chauffeurs,
        'zones': zones,
        'total_chauffeurs': total_chauffeurs,
        'disponibles': disponibles,
        'en_livraison': en_livraison,
        'co2_total_economise': co2_total_economise,
    }
    return render(request, 'admin_panel/chauffeurs/liste.html', context)

@login_required
@user_passes_test(is_admin)
def ajouter_chauffeur(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        nom = request.POST.get('nom')
        telephone = request.POST.get('telephone')
        zone_id = request.POST.get('zone')
        type_vehicule = request.POST.get('type_vehicule')
        immatriculation = request.POST.get('immatriculation')
        capacite = request.POST.get('capacite')
        
        # Créer User
        user = User.objects.create_user(username=username, email=email, password=password, role='Transporteur')
        user.first_name = nom
        user.save()
        
        # Créer Chauffeur
        zone = Zone.objects.get(id=zone_id) if zone_id else None
        Chauffeur.objects.create(
            user=user,
            zone=zone,
            telephone=telephone,
            type_vehicule=type_vehicule,
            immatriculation=immatriculation,
            capacite_max_kg=float(capacite or 100),
            statut='disponible'
        )
        return redirect('admin_panel:chauffeurs')
        
    zones = Zone.objects.all()
    context = {'zones': zones, 'vehicules': Chauffeur.TYPE_VEHICULE}
    return render(request, 'admin_panel/chauffeurs/formulaire.html', context)

@login_required
@user_passes_test(is_admin)
def modifier_chauffeur(request, id):
    chauffeur = get_object_or_404(Chauffeur, id=id)
    if request.method == 'POST':
        chauffeur.user.first_name = request.POST.get('nom')
        chauffeur.user.email = request.POST.get('email')
        chauffeur.user.save()
        
        chauffeur.telephone = request.POST.get('telephone')
        zone_id = request.POST.get('zone')
        chauffeur.zone = Zone.objects.get(id=zone_id) if zone_id else None
        chauffeur.type_vehicule = request.POST.get('type_vehicule')
        chauffeur.immatriculation = request.POST.get('immatriculation')
        capacite = request.POST.get('capacite')
        chauffeur.capacite_max_kg = float(capacite or 100)
        chauffeur.statut = request.POST.get('statut')
        chauffeur.save()
        
        return redirect('admin_panel:chauffeurs')
        
    zones = Zone.objects.all()
    context = {'chauffeur': chauffeur, 'zones': zones, 'vehicules': Chauffeur.TYPE_VEHICULE, 'statuts': Chauffeur.STATUT_CHOICES}
    return render(request, 'admin_panel/chauffeurs/formulaire.html', context)

@login_required
@user_passes_test(is_admin)
def supprimer_chauffeur(request, id):
    chauffeur = get_object_or_404(Chauffeur, id=id)
    if request.method == 'POST':
        # Réassigner missions
        missions = MissionLivraison.objects.filter(chauffeur=chauffeur, statut__in=['assignee', 'acceptee', 'en_route_entrepot', 'colis_pris'])
        reassignees = 0
        if chauffeur.zone:
            autre_chauffeur = Chauffeur.objects.filter(zone=chauffeur.zone, statut='disponible').exclude(id=chauffeur.id).first()
            if autre_chauffeur:
                for m in missions:
                    m.chauffeur = autre_chauffeur
                    m.save()
                    reassignees += 1
        
        user = chauffeur.user
        chauffeur.delete()
        user.delete() # Supprimer aussi le user associé
        
        # En réalité, on pourrait utiliser les messages Django
        return redirect('admin_panel:chauffeurs')
    return redirect('admin_panel:chauffeurs')

@login_required
@user_passes_test(is_admin)
def stats_chauffeur(request, id):
    chauffeur = get_object_or_404(Chauffeur, id=id)
    missions = MissionLivraison.objects.filter(chauffeur=chauffeur, statut='livree').order_by('-date_livraison_effective')
    
    # Graphique livraisons
    # On va simuler les dates pour le chart.js (ou on peut utiliser les vraies)
    
    arbres_plantes = int((chauffeur.total_co2_economise_kg or 0) / 21)
    
    context = {
        'chauffeur': chauffeur,
        'missions': missions,
        'arbres_plantes': arbres_plantes,
    }
    return render(request, 'admin_panel/chauffeurs/stats.html', context)

@login_required
@user_passes_test(is_admin)
def gestion_zones(request):
    zones = Zone.objects.all()
    zones_json = []
    for z in zones:
        zones_json.append({
            'id': z.id,
            'nom': z.nom,
            'ville': z.ville,
            'lat': z.latitude_centre,
            'lng': z.longitude_centre,
            'rayon': z.rayon_km,
            'couleur': z.couleur_hex
        })
        
    context = {
        'zones': zones,
        'zones_json': json.dumps(zones_json)
    }
    return render(request, 'admin_panel/chauffeurs/zones.html', context)

@login_required
@user_passes_test(is_admin)
def ajouter_zone(request):
    if request.method == 'POST':
        nom = request.POST.get('nom')
        ville = request.POST.get('ville')
        lat = request.POST.get('lat')
        lng = request.POST.get('lng')
        rayon = request.POST.get('rayon')
        couleur = request.POST.get('couleur')
        
        Zone.objects.create(
            nom=nom,
            ville=ville,
            latitude_centre=float(lat),
            longitude_centre=float(lng),
            rayon_km=float(rayon),
            couleur_hex=couleur
        )
        return redirect('admin_panel:zones')
    return render(request, 'admin_panel/chauffeurs/ajouter_zone.html')

@login_required
@user_passes_test(is_admin)
def vue_missions(request):
    missions = MissionLivraison.objects.all().order_by('-date_assignation')
    chauffeurs = Chauffeur.objects.filter(latitude_actuelle__isnull=False)
    
    chauffeurs_json = []
    for c in chauffeurs:
        chauffeurs_json.append({
            'nom': c.user.first_name or c.user.username,
            'lat': c.latitude_actuelle,
            'lng': c.longitude_actuelle,
            'statut': c.statut,
            'vehicule': c.type_vehicule,
            'couleur': c.zone.couleur_hex if c.zone else '#000000'
        })
        
    context = {
        'missions': missions,
        'chauffeurs_json': json.dumps(chauffeurs_json)
    }
    return render(request, 'admin_panel/chauffeurs/missions.html', context)

@login_required
@user_passes_test(is_admin)
def assigner_missions(request):
    if request.method == 'POST':
        # Assigner automatiquement
        commandes_attente = Order.objects.filter(status='Payé') # ou 'En traitement'
        
        for commande in commandes_attente:
            # Trouver zone de livraison (simplifié, on se base sur la ville du client par exemple, ou on prend une zone aléatoire pour la demo)
            zone = Zone.objects.first()
            if not zone:
                continue
                
            chauffeur = Chauffeur.objects.filter(zone=zone, statut='disponible').first()
            if chauffeur:
                # Calculer trajet Dijkstra
                entrepot = commande.product.warehouse
                # Pour la démo, on prend des noeuds au hasard
                noeuds_cles = list(noeuds.keys())
                arrivee = noeuds_cles[0] # Simplifié
                
                # Appeler Dijkstra
                depart = "Entrepôt Casablanca"
                res = dijkstra(graphe, depart, arrivee, type_vehicule=chauffeur.type_vehicule)
                
                # Créer Mission
                MissionLivraison.objects.create(
                    chauffeur=chauffeur,
                    commande=commande,
                    entrepot=entrepot,
                    statut='assignee',
                    trajet_json=res,
                    distance_km=res['distance_km'],
                    co2_estime_kg=res['co2_optimise_kg'],
                    co2_mode_classique_kg=res['co2_classique_kg'],
                    co2_economise_kg=res['co2_economise_kg']
                )
                
                commande.status = 'En livraison'
                commande.save()
                
        return redirect('admin_panel:missions')
    return redirect('admin_panel:missions')
