import os
import django
import random
from datetime import datetime, timedelta
from django.utils import timezone

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "atlas_logistics.settings")
django.setup()

from apps.authentication.models import User
from apps.logistics_core.models import Warehouse, Product
from apps.client.models import Order
from apps.transporter.models import Chauffeur, Zone, MissionLivraison, TourneeJournaliere
from apps.transporter.algorithms.dijkstra_tournee import dijkstra, graphe, noeuds

def seed_demo():
    print("--- Demarrage de la generation des donnees professionnelles ---")

    # 1. Nettoyage des données existantes
    print("--- Nettoyage des anciennes donnees ---")
    TourneeJournaliere.objects.all().delete()
    MissionLivraison.objects.all().delete()
    Order.objects.all().delete()
    Product.objects.all().delete()
    Chauffeur.objects.all().delete()
    Zone.objects.all().delete()
    # On garde les admins et les entrepôts
    User.objects.exclude(role='Admin').exclude(is_superuser=True).delete()

    # 2. Création des Hubs (Entrepôts) - REBOOT COMPLET
    print("--- Nettoyage et Recreation des Hubs ---")
    Warehouse.objects.all().delete()
    
    hubs_data = [
        # Casablanca
        ("Hub Casa-Oukacha (Est)", "Casablanca", 33.6050, -7.5300, 14, 10),
        ("Hub Casa-Nouaceur (Zone Aero)", "Casablanca", 33.3675, -7.5898, 12, 8),
        # Marrakech
        ("Hub Marrakech-Sidi Ghanem", "Marrakech", 31.6500, -8.0300, 10, 6),
        ("Hub Marrakech-Sud (Route Ourika)", "Marrakech", 31.5800, -7.9500, 10, 6),
        # Tanger
        ("Hub Tanger-Ville (Zone Franche)", "Tanger", 35.7200, -5.8500, 12, 8),
        ("Hub Tanger-Moghogha (Logistique)", "Tanger", 35.7500, -5.7800, 16, 12),
        # Nouvelles Villes
        ("Hub Fès-Saïss", "Fès", 33.9300, -4.9800, 10, 6),
        ("Hub Agadir-Aït Melloul", "Agadir", 30.3400, -9.4900, 12, 8),
        ("Hub Béni Mellal-Tadla", "Béni Mellal", 32.3373, -6.3498, 8, 4),
    ]
    
    hubs = []
    for name, city, lat, lng, rails, shelves in hubs_data:
        h = Warehouse.objects.create(name=name, city=city, lat=lat, lng=lng, capacity=5000, total_rails=rails, total_shelves=shelves)
        hubs.append(h)
    
    # 3. Création des 4 PME Marocaines
    print("--- Creation des 4 PMEs ---")
    smes = [
        {
            "name": "EcoLife Morocco",
            "username": "ecolife_ma",
            "email": "contact@ecolife.ma",
            "city": "Casablanca",
            "products": [
                ("Gourde Inox Isotherme", "Eco", 120, 0.5),
                ("Lunch Box Bambou", "Eco", 150, 0.4),
                ("Sac Isotherme Recyclé", "Eco", 80, 0.6),
                ("Tasse Réutilisable", "Eco", 60, 0.3),
                ("Boîte Alimentaire Verre", "Eco", 110, 0.7)
            ]
        },
        {
            "name": "Atlas Apparel",
            "username": "atlas_apparel",
            "email": "sales@atlas-apparel.ma",
            "city": "Marrakech",
            "products": [
                ("Hoodie Atlas Premium", "Textile", 280, 1.2),
                ("T-shirt Coton Bio", "Textile", 150, 0.8),
                ("Jogging Confort", "Textile", 250, 1.5),
                ("Casquette Signature", "Textile", 120, 0.4),
                ("Chemise en Lin", "Textile", 320, 1.1)
            ]
        },
        {
            "name": "Artisanat du Souss",
            "username": "artisanat_souss",
            "email": "contact@artisanat-souss.ma",
            "city": "Tanger", # On change pour Tanger pour varier
            "products": [
                ("Huile d'Argan Bio (250ml)", "Bio", 180, 0.3),
                ("Savon Noir Traditionnel", "Bio", 45, 0.5),
                ("Tapis Berbère Artisanal", "Artisanat", 1200, 5.0),
                ("Bougie Parfumée Fleur d'Oranger", "Déco", 95, 0.4),
                ("Coffret Découverte Maroc", "Bio", 350, 1.8)
            ]
        },
        {
            "name": "Vitality Bio Maroc",
            "username": "vitality_bio",
            "email": "order@vitality.ma",
            "city": "Casablanca",
            "products": [
                ("Magnésium Marin B6", "Santé", 145, 0.1),
                ("Oméga 3 Premium", "Santé", 195, 0.1),
                ("Spiruline Bio (Poudre)", "Santé", 120, 0.1),
                ("Vitamine C Liposomale", "Santé", 160, 0.1),
                ("Collagène Marin", "Santé", 250, 0.1),
                ("Probiotiques 10 Souches", "Santé", 180, 0.1)
            ]
        }
    ]

    created_smes = []
    for sme_data in smes:
        user = User.objects.create_user(
            username=sme_data["username"],
            email=sme_data["email"],
            password="123",
            role="Entreprise",
            company_name=sme_data["name"]
        )
        created_smes.append(user)
        
        # Trouver les entrepôts de la ville ou utiliser tous les hubs
        city_hubs = [h for h in hubs if h.city == sme_data["city"]]
        if not city_hubs: city_hubs = hubs
        
        for p_name, cat, price, co2 in sme_data["products"]:
            # On remplit modérément (1-2 emplacements par produit par ville cible)
            city_hubs = [h for h in hubs if h.city == sme_data["city"]]
            if not city_hubs: city_hubs = [random.choice(hubs)]
            
            for h in city_hubs:
                Product.objects.create(
                    name=p_name,
                    category=cat,
                    price=price,
                    stock=random.randint(100, 500),
                    co2_impact=co2,
                    warehouse=h,
                    seller=user,
                    rail=random.randint(1, h.total_rails),
                    shelf=random.randint(1, h.total_shelves)
                )
    
    # 4. Création des 20 Clients
    print("--- Creation des clients ---")
    client_names = [
        ("Youssef", "Alami", "Casablanca"), ("Amine", "Berrada", "Rabat"),
        ("Zineb", "Bennani", "Tanger"), ("Mehdi", "Tazi", "Marrakech"),
        ("Fatine", "Idrissi", "Fès"), ("Omar", "Mansouri", "Agadir"),
        ("Sara", "El Fassi", "Casablanca"), ("Hassan", "Bouzidi", "Oujda"),
        ("Layla", "Kadiri", "Rabat"), ("Anas", "Slaoui", "Marrakech"),
        ("Driss", "Mansour", "Casablanca"), ("Salma", "Tazi", "Rabat"),
        ("Hamza", "Berrada", "Tanger"), ("Ghita", "Alami", "Fès"),
        ("Kamal", "Idrissi", "Marrakech"), ("Najat", "Bennani", "Agadir"),
        ("Adil", "Slaoui", "Béni Mellal"), ("Meryem", "Mansouri", "Béni Mellal"),
        ("Yassine", "Zidani", "Casablanca"), ("Sami", "Kadiri", "Rabat")
    ]
    
    created_clients = []
    for first, last, city in client_names:
        username = f"{first.lower()}_{last.lower()}"
        u = User.objects.create_user(
            username=username,
            email=f"{username}@gmail.com",
            password="123",
            role="Client",
            first_name=first,
            last_name=last
        )
        created_clients.append(u)

    # 5. Création des Zones et 20 Chauffeurs
    print("--- Creation des zones et chauffeurs ---")
    zones_data = [
        ("Zone Centre", "Casablanca", 33.5731, -7.5898, "#10B981"),
        ("Zone Nord", "Tanger", 35.7595, -5.8340, "#3B82F6"),
        ("Zone Sud", "Marrakech", 31.6295, -7.9811, "#F59E0B"),
        ("Zone Est", "Fès", 34.0181, -5.0078, "#8B5CF6"),
        ("Zone Souss", "Agadir", 30.4278, -9.5981, "#EC4899"),
        ("Zone Tadla", "Béni Mellal", 32.3373, -6.3498, "#EF4444"),
    ]
    
    zones = []
    for nom, ville, lat, lng, color in zones_data:
        z = Zone.objects.create(nom=nom, ville=ville, latitude_centre=lat, longitude_centre=lng, couleur_hex=color)
        zones.append(z)

    names_pool = ["Ahmed", "Karim", "Meryem", "Said", "Noura", "Rachid", "Hicham", "Khadija", "Yassine", "Samira", 
                  "Omar", "Layla", "Anas", "Fatima", "Driss", "Zineb", "Hamza", "Ghita", "Kamal", "Salma"]
    vehicles = [
        ("Renault Master", "camionnette", 800), ("Ford Transit", "camionnette", 900),
        ("Fiat Doblo", "camionnette", 500), ("Kangoo", "voiture", 300),
        ("Peugeot Partner", "voiture", 350)
    ]
    
    created_drivers = []
    # On s'assure d'avoir au moins 1 chauffeur par ville cible pour la demo
    target_cities = ["Casablanca", "Tanger", "Fès", "Marrakech", "Agadir", "Béni Mellal"]
    
    for i, name in enumerate(names_pool):
        username = f"driver_{name.lower()}"
        # On evite les doublons de username si la liste de noms a des redites
        if User.objects.filter(username=username).exists():
            username = f"driver_{name.lower()}_{i}"
            
        u = User.objects.create_user(
            username=username,
            email=f"{username}@atlas-logistics.ma",
            password="123",
            role="Transporteur",
            first_name=name
        )
        
        v_name, v_type, v_cap = random.choice(vehicles)
        
        # Attribution de zone : on boucle sur les villes cibles pour en avoir partout
        city_name = target_cities[i % len(target_cities)]
        zone = next(z for z in zones if z.ville == city_name)
        
        d = Chauffeur.objects.create(
            user=u,
            zone=zone,
            telephone=f"0661{random.randint(100000, 999999)}",
            type_vehicule=v_type,
            immatriculation=f"{random.randint(1000, 9999)}|A|{random.randint(1, 99)}",
            capacite_max_kg=v_cap,
            statut='disponible',
            latitude_actuelle=zone.latitude_centre + random.uniform(-0.01, 0.01),
            longitude_actuelle=zone.longitude_centre + random.uniform(-0.01, 0.01),
            total_livraisons=random.randint(50, 150),
            total_co2_economise_kg=random.uniform(200, 500)
        )
        created_drivers.append(d)


    # 6. Simulation d'activité (Commandes et Missions)
    print("--- Simulation de l'activite historique ---")
    all_products = list(Product.objects.all())
    
    # 6a. Commandes Livrées (Passé)
    for _ in range(50):
        client = random.choice(created_clients)
        product = random.choice(all_products)
        qty = random.randint(1, 3)
        date = timezone.now() - timedelta(days=random.randint(2, 30))
        
        order = Order.objects.create(
            client=client,
            product=product,
            status='Livrée',
            order_date=date,
            price_total=product.price * qty,
            co2_emission=product.co2_impact * qty,
            quantity=qty
        )
        
        # Créer une mission terminée
        driver = random.choice(created_drivers)
        MissionLivraison.objects.create(
            chauffeur=driver,
            commande=order,
            entrepot=product.warehouse,
            statut='livree',
            distance_km=random.uniform(5, 40),
            co2_estime_kg=order.co2_emission,
            date_livraison_effective=date + timedelta(hours=random.randint(1, 4))
        )

    # 6b. Commandes Actives (Pour la démo)
    print("--- Creation des missions actives pour la demonstration ---")
    
    noeuds_cles = list(noeuds.keys())
    
    # Helper for distance
    def simple_dist(lat1, lng1, lat2, lng2):
        return (lat1 - lat2)**2 + (lng1 - lng2)**2

    for driver in created_drivers:
        # 1. Trouver l'entrepôt le plus proche du chauffeur dans sa ville
        city_hubs = [h for h in hubs if h.city == driver.zone.ville]
        if not city_hubs:
            selected_warehouse = random.choice(hubs)
        else:
            selected_warehouse = min(city_hubs, key=lambda h: simple_dist(h.lat, h.lng, driver.latitude_actuelle, driver.longitude_actuelle))
        
        # 2. Prendre des produits de cet entrepôt
        warehouse_products = [p for p in all_products if p.warehouse == selected_warehouse]
        if not warehouse_products:
            warehouse_products = [p for p in all_products if p.warehouse.city == driver.zone.ville]
        
        if not warehouse_products:
            warehouse_products = all_products

        # Give each driver 3 to 5 active missions
        for _ in range(random.randint(3, 5)):
            client = random.choice(created_clients)
            product = random.choice(warehouse_products)
            
            order = Order.objects.create(
                client=client,
                product=product,
                status='En livraison',
                order_date=timezone.now() - timedelta(hours=random.randint(1, 5)),
                price_total=product.price,
                co2_emission=product.co2_impact,
                quantity=1
            )
            
            # Dijkstra pour le trajet
            depart = f"Entrepôt {selected_warehouse.city}"
            if depart not in noeuds:
                depart = "Entrepôt Casablanca"
            
            arrivee = random.choice(noeuds_cles)
            while "Entrepôt" in arrivee:
                arrivee = random.choice(noeuds_cles)
                
            path_res = dijkstra(graphe, depart, arrivee, type_vehicule=driver.type_vehicule)
            
            MissionLivraison.objects.create(
                chauffeur=driver,
                commande=order,
                entrepot=selected_warehouse,
                statut='en_livraison',
                trajet_json=path_res,
                distance_km=path_res['distance_km'],
                co2_estime_kg=path_res['co2_optimise_kg'],
                co2_mode_classique_kg=path_res['co2_classique_kg'],
                co2_economise_kg=path_res['co2_economise_kg']
            )
            
            driver.statut = 'en_livraison'
            driver.save()


    print("\n--- Simulation terminee avec succes ! ---")
    print(f"- {len(created_smes)} PMEs créées.")
    print(f"- {len(all_products)} Produits générés.")
    print(f"- {len(created_clients)} Clients marocains.")
    print(f"- {len(created_drivers)} Chauffeurs opérationnels.")
    print(f"- {Order.objects.count()} Commandes au total.")
    print(f"- {MissionLivraison.objects.filter(statut='en_livraison').count()} Missions actives pour la démo.")

if __name__ == "__main__":
    seed_demo()
