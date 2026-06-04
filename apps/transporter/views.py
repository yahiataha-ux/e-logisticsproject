import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from .models import Chauffeur, MissionLivraison, Zone
from apps.logistics_core.models import Warehouse
from django.db.models import Sum

@login_required
def dashboard_chauffeur(request):
    try:
        chauffeur = request.user.chauffeur
    except Chauffeur.DoesNotExist:
        return redirect('home')

    missions_du_jour = MissionLivraison.objects.filter(
        chauffeur=chauffeur,
        date_assignation__date=timezone.now().date()
    ).order_by('id')

    missions_en_cours = missions_du_jour.exclude(statut__in=['livree', 'echec']).select_related('commande', 'entrepot')
    
    total_km = missions_du_jour.aggregate(Sum('distance_km'))['distance_km__sum'] or 0
    co2_eco = missions_du_jour.aggregate(Sum('co2_economise_kg'))['co2_economise_kg__sum'] or 0
    co2_emis = missions_du_jour.aggregate(Sum('co2_estime_kg'))['co2_estime_kg__sum'] or 0

    # Construction des tournées dynamiques pour ce chauffeur
    tournees_dict = {}
    import random
    
    city_coords = {
        'Casablanca': (33.5731, -7.5898), 'Rabat': (34.0209, -6.8416),
        'Tanger': (35.7595, -5.8340), 'Marrakech': (31.6295, -7.9811),
        'Agadir': (30.4278, -9.5981), 'Fès': (34.0181, -5.0078),
        'Oujda': (34.6867, -1.9114), 'Béni Mellal': (32.3373, -6.3498),
    }
    
    # Initialiser tous les hubs de la ville du chauffeur pour la visibilité
    local_hubs = Warehouse.objects.filter(city=chauffeur.zone.ville)
    for wh in local_hubs:
        hub_key = f"{wh.city}_{wh.id}"
        tournees_dict[hub_key] = {
            'id': f'tournee_{wh.id}',
            'name': f'Hub {wh.city} ({wh.name})',
            'couleur': random.choice(['#22C55E', '#6366F1', '#F97316', '#3b82f6', '#8b5cf6']),
            'entrepot': [wh.lat, wh.lng] if (wh.lat and wh.lng) else city_coords.get(wh.city, (33.5, -7.5)),
            'arrets': []
        }

    for m in missions_en_cours:
        wh = m.entrepot
        if not wh: continue
        
        hub_key = f"{wh.city}_{wh.id}"
        # Si par hasard la mission vient d'un entrepôt hors zone du chauffeur
        if hub_key not in tournees_dict:
            tournees_dict[hub_key] = {
                'id': f'tournee_{wh.id}',
                'name': f'Hub {wh.city} ({wh.name})',
                'couleur': random.choice(['#22C55E', '#6366F1', '#F97316', '#3b82f6', '#8b5cf6']),
                'entrepot': [wh.lat, wh.lng] if (wh.lat and wh.lng) else city_coords.get(wh.city, (33.5, -7.5)),
                'arrets': []
            }
            
        client = m.commande.client
        client_city = getattr(client, 'city', wh.city)
        base_lat, base_lng = city_coords.get(client_city, tournees_dict[hub_key]['entrepot'])
        lat = base_lat + random.uniform(-0.02, 0.02)
        lng = base_lng + random.uniform(-0.02, 0.02)
        
        tournees_dict[hub_key]['arrets'].append({
            'latlng': [lat, lng],
            'infos': {
                'tournee': wh.city,
                'client': client.get_full_name() or client.username,
                'adresse': client_city,
                'colis': f"{m.commande.quantity} colis",
                'co2': m.co2_estime_kg
            }
        })
        
    # Optimisation de l'ordre des arrêts (Plus proche voisin)
    for hub_key, t in tournees_dict.items():
        if not t['arrets']: continue
        
        optimized = []
        unvisited = t['arrets'][:]
        current_pos = t['entrepot']
        
        while unvisited:
            # Distance euclidienne simplifiée pour le tri
            nearest = min(unvisited, key=lambda a: (a['latlng'][0] - current_pos[0])**2 + (a['latlng'][1] - current_pos[1])**2)
            optimized.append(nearest)
            unvisited.remove(nearest)
            current_pos = nearest['latlng']
            
        # Réassigner les numéros dans l'ordre optimisé
        for i, stop in enumerate(optimized):
            stop['num'] = i + 1
            
        t['arrets'] = optimized
        
    tournees_json = json.dumps(list(tournees_dict.values()))

    context = {
        'chauffeur': chauffeur,
        'missions': missions_en_cours,
        'total_km': total_km,
        'co2_eco': co2_eco,
        'co2_emis': co2_emis,
        'missions_terminees': missions_du_jour.filter(statut='livree').count(),
        'tournees_json': tournees_json
    }
    return render(request, 'chauffeur/dashboard.html', context)


@login_required
def mission_detail(request, id):
    chauffeur = get_object_or_404(Chauffeur, user=request.user)
    mission = get_object_or_404(MissionLivraison, id=id, chauffeur=chauffeur)
    
    context = {
        'chauffeur': chauffeur,
        'mission': mission,
    }
    return render(request, 'chauffeur/mission_detail.html', context)


@login_required
def marquer_livre(request, id):
    chauffeur = get_object_or_404(Chauffeur, user=request.user)
    mission = get_object_or_404(MissionLivraison, id=id, chauffeur=chauffeur)
    
    mission.statut = 'livree'
    mission.date_livraison_effective = timezone.now()
    mission.save()
    
    chauffeur.total_livraisons += 1
    if mission.co2_economise_kg:
        chauffeur.total_co2_economise_kg += mission.co2_economise_kg
    chauffeur.save()
    
    return redirect('transporter:dashboard')


@login_required
def signaler_probleme(request, id):
    chauffeur = get_object_or_404(Chauffeur, user=request.user)
    mission = get_object_or_404(MissionLivraison, id=id, chauffeur=chauffeur)
    
    if request.method == 'POST':
        motif = request.POST.get('motif', '')
        mission.statut = 'echec'
        mission.commentaire_client = f"PROBLÈME: {motif}"
        mission.save()
        return redirect('transporter:dashboard')
        
    return redirect('transporter:mission_detail', id=id)


@login_required
def historique_chauffeur(request):
    chauffeur = get_object_or_404(Chauffeur, user=request.user)
    missions = MissionLivraison.objects.filter(chauffeur=chauffeur, statut__in=['livree', 'echec']).order_by('-date_livraison_effective')
    
    arbres_plantes = int(chauffeur.total_co2_economise_kg / 21) # 1 tree absorbs ~21kg CO2 per year
    
    niveau = "🥉 Junior"
    if chauffeur.total_livraisons > 500:
        niveau = "🏆 Elite"
    elif chauffeur.total_livraisons > 200:
        niveau = "🥇 Expert"
    elif chauffeur.total_livraisons > 50:
        niveau = "🥈 Confirmé"

    context = {
        'chauffeur': chauffeur,
        'missions': missions,
        'arbres_plantes': arbres_plantes,
        'niveau': niveau,
    }
    return render(request, 'chauffeur/historique.html', context)


@login_required
def notifications_chauffeur(request):
    chauffeur = get_object_or_404(Chauffeur, user=request.user)
    # Dans un vrai système, on aurait un modèle Notification.
    # On simule ici.
    notifications = [
        {"titre": "Nouvelle zone assignée", "message": f"Vous avez été assigné à la zone {chauffeur.zone.nom if chauffeur.zone else 'Aucune'}", "date": timezone.now()},
        {"titre": "Objectif CO2", "message": "Vous avez économisé plus de 10kg de CO2 cette semaine !", "date": timezone.now() - timezone.timedelta(days=1)}
    ]
    return render(request, 'chauffeur/notifications.html', {'notifications': notifications, 'chauffeur': chauffeur})


@login_required
def changer_statut(request):
    if request.method == 'POST':
        chauffeur = get_object_or_404(Chauffeur, user=request.user)
        nouveau_statut = request.POST.get('statut')
        if nouveau_statut in dict(Chauffeur.STATUT_CHOICES):
            chauffeur.statut = nouveau_statut
            chauffeur.save()
    return redirect('transporter:dashboard')


# APIs
@login_required
def api_positions_chauffeurs(request):
    chauffeurs = Chauffeur.objects.filter(user__is_active=True)
    data = []
    for c in chauffeurs:
        if c.latitude_actuelle and c.longitude_actuelle:
            data.append({
                'id': c.id,
                'nom': c.user.username,
                'lat': c.latitude_actuelle,
                'lng': c.longitude_actuelle,
                'statut': c.statut,
                'vehicule': c.type_vehicule
            })
    return JsonResponse(data, safe=False)

@login_required
def api_statut_mission(request, id):
    mission = get_object_or_404(MissionLivraison, id=id)
    return JsonResponse({'id': mission.id, 'statut': mission.statut})
