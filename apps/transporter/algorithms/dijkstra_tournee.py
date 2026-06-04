import math

# GRAPHE DE BASE (à étendre)
noeuds = {
    "Entrepôt Casablanca": (33.5731, -7.5898),
    "Hay Hassani": (33.5557, -7.6453),
    "Ain Chock": (33.5333, -7.5833),
    "Sidi Bernoussi": (33.6014, -7.5019),
    "Ain Sebaa": (33.6167, -7.5167),
    "Derb Sultan": (33.5806, -7.6167),
    "Maarif": (33.5681, -7.6336),
    "Anfa": (33.5833, -7.6500),
    "Entrepôt Rabat": (34.0209, -6.8416),
    "Agdal Rabat": (33.9911, -6.8508),
    "Souissi": (33.9833, -6.8167),
    "Salé Centre": (34.0333, -6.8000),
    "Entrepôt Tanger": (35.7595, -5.8340),
    "Tanger Ville": (35.7800, -5.8100),
    "Malabata": (35.7900, -5.7800),
}

def haversine_distance(coord1, coord2):
    R = 6371.0 # Radius of the Earth in km
    lat1, lon1 = math.radians(coord1[0]), math.radians(coord1[1])
    lat2, lon2 = math.radians(coord2[0]), math.radians(coord2[1])
    
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return R * c

# Build a fully connected graph with haversine distances
graphe = {}
for n1, c1 in noeuds.items():
    graphe[n1] = {}
    for n2, c2 in noeuds.items():
        if n1 != n2:
            # Multiplied by 1.3 to simulate actual road distance instead of straight line
            graphe[n1][n2] = haversine_distance(c1, c2) * 1.3

def dijkstra(graphe_dict, depart, arrivee, critere="distance", type_vehicule="camionnette"):
    """
    critere = "distance" | "co2" | "combine"
    Retourne : {
      "chemin": [liste noeuds],
      "distance_km": float,
      "duree_estimee_min": int,
      "co2_optimise_kg": float,
      "co2_classique_kg": float,  # trajet direct non optimisé
      "co2_economise_kg": float,
      "economie_pourcentage": float
    }
    """
    
    # Priority queue implementation
    distances = {node: float('inf') for node in graphe_dict}
    distances[depart] = 0
    predecessors = {node: None for node in graphe_dict}
    unvisited = list(graphe_dict.keys())
    
    while unvisited:
        # Get node with minimum distance
        current = min(unvisited, key=lambda node: distances[node])
        
        if distances[current] == float('inf'):
            break
            
        if current == arrivee:
            break
            
        unvisited.remove(current)
        
        for neighbor, weight in graphe_dict[current].items():
            # Apply criteria factor if needed, here we just use distance since CO2 is proportional
            # We can use different weights if different road types have different CO2 factors, 
            # but for this simulation we'll just use the distance.
            new_distance = distances[current] + weight
            
            if new_distance < distances[neighbor]:
                distances[neighbor] = new_distance
                predecessors[neighbor] = current

    # Reconstruct path
    path = []
    current = arrivee
    while current is not None:
        path.insert(0, current)
        current = predecessors[current]
        
    distance_km = distances[arrivee]
    if distance_km == float('inf'):
        distance_km = 0
        path = [depart, arrivee]
        
    duree_estimee_min = int(distance_km * 2) # Average speed of 30km/h in city (1km = 2min)
    
    co2_optimise_kg = calculer_co2(distance_km, type_vehicule)
    distance_classique = distance_km * 1.35 # Reference +35% distance
    co2_classique_kg = calculer_co2(distance_classique, type_vehicule)
    co2_economise_kg = co2_classique_kg - co2_optimise_kg
    
    economie_pourcentage = 0
    if co2_classique_kg > 0:
        economie_pourcentage = (co2_economise_kg / co2_classique_kg) * 100
        
    return {
        "chemin": path,
        "distance_km": round(distance_km, 2),
        "duree_estimee_min": duree_estimee_min,
        "co2_optimise_kg": round(co2_optimise_kg, 2),
        "co2_classique_kg": round(co2_classique_kg, 2),
        "co2_economise_kg": round(co2_economise_kg, 2),
        "economie_pourcentage": round(economie_pourcentage, 2)
    }

def optimiser_tournee(entrepot, liste_clients):
    """
    Algorithme du voyageur de commerce simplifié (greedy nearest neighbor)
    Ordonne les livraisons pour minimiser distance totale
    Retourne : ordre optimal des arrêts + métriques CO2
    """
    if not liste_clients:
        return []
        
    unvisited = liste_clients[:]
    current = entrepot
    tournee = []
    
    while unvisited:
        # Find nearest neighbor
        nearest = min(unvisited, key=lambda c: graphe.get(current, {}).get(c, float('inf')))
        tournee.append(nearest)
        unvisited.remove(nearest)
        current = nearest
        
    return tournee

def calculer_co2(distance_km, type_vehicule):
    """
    Facteurs d'émission par type de véhicule :
    moto: 0.08 kgCO2/km
    voiture: 0.15 kgCO2/km  
    camionnette: 0.22 kgCO2/km
    camion: 0.35 kgCO2/km
    """
    facteurs = {
        'moto': 0.08,
        'voiture': 0.15,
        'camionnette': 0.22,
        'camion': 0.35
    }
    facteur = facteurs.get(type_vehicule, 0.22)
    return distance_km * facteur
