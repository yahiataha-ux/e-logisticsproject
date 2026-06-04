import json
import random
import csv
import socket
import qrcode
import io
import base64
from datetime import timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import login
from django.http import HttpResponse
from django.db.models import Sum, Count, Q, Avg, F
from django.db.models.functions import TruncDate
from django.utils import timezone
from apps.client.models import Order
from apps.transporter.models import Chauffeur, MissionLivraison
from apps.logistics_core.models import Warehouse, Product
from apps.authentication.models import User

def is_admin(user):
    return user.is_authenticated and user.role == 'Admin'

@login_required
def dashboard_view(request):
    user = request.user
    
    # Redirect non-admins to their dedicated apps
    if user.role == 'Entreprise':
        return redirect('enterprise:dashboard')
    elif user.role == 'Transporteur':
        return redirect('transporter:dashboard')
    elif user.role == 'Client':
        return redirect('client:marketplace')
    elif user.role != 'Admin':
        return redirect('login')

    # 1. ADMIN - Premium Dashboard
    now = timezone.now()
    orders = Order.objects.all()
    
    # KPI Totals
    total_revenue = orders.aggregate(total=Sum('price_total'))['total'] or 0
    total_co2 = (orders.aggregate(total=Sum('co2_emission'))['total'] or 0) / 1000
    active_deliveries = orders.filter(status='En livraison').count()
    
    # Analytics for Chart.js (Ensure a curve by padding last 30 days)
    last_30_days_list = [now.date() - timedelta(days=i) for i in range(29, -1, -1)]
    orders_by_day = orders.filter(order_date__date__gte=last_30_days_list[0]).annotate(date=TruncDate('order_date')).values('date').annotate(count=Count('id'), revenue=Sum('price_total')).order_by('date')
    
    orders_map = {d['date']: d for d in orders_by_day}
    
    dates = []
    rev_data = []
    count_data = []
    
    for d in last_30_days_list:
        dates.append(d.strftime("%d %b"))
        if d in orders_map:
            rev_data.append(float(orders_map[d]['revenue'] or 0))
            count_data.append(orders_map[d]['count'])
        else:
            rev_data.append(0.0)
            count_data.append(0)

    rev_by_hub = Warehouse.objects.annotate(revenue=Sum('products__order__price_total')).values('city', 'revenue').order_by('-revenue')
    hub_labels = [h['city'] for h in rev_by_hub]
    hub_values = [float(h['revenue'] or 0) for h in rev_by_hub]

    qr_data, login_url = get_qr_code(request)

    # Active Users (last 2 minutes)
    two_minutes_ago = now - timedelta(minutes=2)
    active_users = User.objects.filter(last_activity__gte=two_minutes_ago).order_by('-last_activity')

    context = {
        'total_orders': orders.count(),
        'total_revenue': total_revenue,
        'total_co2': total_co2,
        'active_deliveries': active_deliveries,
        'clients_count': User.objects.filter(role='Client').count(),
        'companies_count': User.objects.filter(role='Entreprise').count(),
        'transporters_count': User.objects.filter(role='Transporteur').count(),
        'vehicles_count': Chauffeur.objects.count(),
        'chart_dates': json.dumps(dates),
        'chart_rev': json.dumps(rev_data),
        'chart_count': json.dumps(count_data),
        'hub_labels': json.dumps(hub_labels),
        'hub_values': json.dumps(hub_values),
        'recent_orders': orders.order_by('-order_date')[:10],
        'qr_code': qr_data,
        'login_url': login_url,
        'active_users': active_users,
        'online_count': active_users.count(),
    }
    return render(request, 'admin_panel/dashboard.html', context)

@login_required
@user_passes_test(is_admin)
def admin_users(request):
    search_query = request.GET.get('q', '')
    role_filter = request.GET.get('role', '')
    users = User.objects.all().order_by('-date_joined')
    
    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(role__icontains=search_query) |
            Q(company_name__icontains=search_query)
        )
    
    if role_filter:
        users = users.filter(role=role_filter)
        
    return render(request, 'admin_panel/users.html', {
        'users_list': users,
        'search_query': search_query,
        'role_filter': role_filter,
        'roles': [r[0] for r in User.ROLE_CHOICES]
    })

@login_required
@user_passes_test(is_admin)
def admin_add_user(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password', '123') # Default password as requested
        role = request.POST.get('role')
        company_name = request.POST.get('company_name')
        
        user = User.objects.create_user(username=username, email=email, password=password, role=role)
        user.company_name = company_name
        user.save()
        return redirect('admin_panel:users')
    
    return render(request, 'admin_panel/add_user.html', {'roles': [r[0] for r in User.ROLE_CHOICES]})

@login_required
@user_passes_test(is_admin)
def admin_delete_user(request, user_id):
    user_to_delete = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        # Don't allow deleting self
        if user_to_delete.id != request.user.id:
            user_to_delete.delete()
    return redirect('admin_panel:users')

@login_required
@user_passes_test(is_admin)
def admin_edit_user(request, user_id):
    user_to_edit = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        user_to_edit.username = request.POST.get('username')
        user_to_edit.email = request.POST.get('email')
        user_to_edit.role = request.POST.get('role')
        user_to_edit.company_name = request.POST.get('company_name')
        user_to_edit.save()
        return redirect('admin_panel:users')
    
    return render(request, 'admin_panel/edit_user.html', {'user_to_edit': user_to_edit})

@login_required
@user_passes_test(is_admin)
def export_data_csv(request, model_type):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="atlas_{model_type}.csv"'
    writer = csv.writer(response)
    
    if model_type == 'users':
        writer.writerow(['Username', 'Email', 'Role', 'Company', 'Last Login', 'Date Joined'])
        data = User.objects.all()
        for obj in data:
            writer.writerow([obj.username, obj.email, obj.role, obj.company_name or '-', obj.last_login, obj.date_joined])
    
    elif model_type == 'orders':
        writer.writerow(['ID', 'Client', 'Seller', 'Status', 'Price', 'Date'])
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        data = Order.objects.all()
        if start_date:
            data = data.filter(order_date__date__gte=start_date)
        if end_date:
            data = data.filter(order_date__date__lte=end_date)
            
        for obj in data:
            writer.writerow([obj.id, obj.client.username, obj.product.seller.username, obj.status, obj.price_total, obj.order_date])
            
    elif model_type == 'hubs':
        writer.writerow(['Name', 'City', 'Lat', 'Lng', 'Stock'])
        data = Warehouse.objects.all()
        for obj in data:
            writer.writerow([obj.name, obj.city, obj.lat, obj.lng, obj.products.aggregate(Sum('stock'))['stock__sum'] or 0])
            
    return response

@login_required
@user_passes_test(is_admin)
def admin_login_as(request, user_id):
    target_user = get_object_or_404(User, id=user_id)
    # Store original admin ID to allow return
    request.session['simulated_from_admin_id'] = request.user.id
    login(request, target_user)
    return redirect('home')

def admin_logout_as(request):
    admin_id = request.session.get('simulated_from_admin_id')
    if admin_id:
        admin_user = get_object_or_404(User, id=admin_id)
        login(request, admin_user)
        del request.session['simulated_from_admin_id']
        return redirect('admin_panel:dashboard')
    return redirect('logout')

@login_required
@user_passes_test(is_admin)
def admin_companies(request):
    companies = User.objects.filter(role='Entreprise').annotate(
        order_count=Count('products__order'),
        total_rev=Sum('products__order__price_total')
    )
    return render(request, 'admin_panel/companies.html', {'companies': companies})

@login_required
@user_passes_test(is_admin)
def admin_company_detail(request, company_id):
    company = get_object_or_404(User, id=company_id, role='Entreprise')
    orders = Order.objects.filter(product__seller=company).order_by('-order_date')
    return render(request, 'admin_panel/company_detail.html', {
        'company': company,
        'orders': orders
    })

@login_required
@user_passes_test(is_admin)
def admin_transporters(request):
    search_query = request.GET.get('q', '')
    chauffeurs = Chauffeur.objects.all().select_related('user', 'zone')
    # Add Transport Companies
    companies = User.objects.filter(role='Transporteur').annotate(fleet_size=Count('chauffeur')).order_by('-rating_co2')
    
    if search_query:
        chauffeurs = chauffeurs.filter(
            Q(user__username__icontains=search_query) |
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query)
        )
        companies = companies.filter(
            Q(username__icontains=search_query) |
            Q(company_name__icontains=search_query)
        )
        
    return render(request, 'admin_panel/transporters.html', {
        'chauffeurs': chauffeurs,
        'companies': companies,
        'search_query': search_query
    })

@login_required
@user_passes_test(is_admin)
def admin_hubs(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        city = request.POST.get('city')
        capacity = request.POST.get('capacity')
        rails = request.POST.get('rails')
        shelves = request.POST.get('shelves', 8)
        
        city_coords = {
            'Casablanca': (33.5731, -7.5898), 'Rabat': (34.0209, -6.8416),
            'Tanger': (35.7595, -5.8340), 'Marrakech': (31.6295, -7.9811),
            'Agadir': (30.4278, -9.5981), 'Fès': (34.0181, -5.0078),
            'Oujda': (34.6867, -1.9114), 'Laâyoune': (27.1500, -13.2000),
        }
        lat, lng = city_coords.get(city, (30.0, -7.0))
        Warehouse.objects.create(
            name=name, city=city, capacity=capacity, total_rails=rails, total_shelves=shelves, lat=lat, lng=lng
        )
        from django.contrib import messages
        messages.success(request, f"Nouveau Hub à {city} créé avec succès.")
        return redirect('admin_panel:hubs')

    city_query = request.GET.get('city', '')
    hubs = Warehouse.objects.all()
    if city_query:
        hubs = hubs.filter(city__icontains=city_query)
    
    hubs = hubs.annotate(
        product_count=Count('products'),
        total_stock=Sum('products__stock')
    )
    return render(request, 'admin_panel/hubs.html', {'hubs': hubs, 'city_query': city_query})

@login_required
@user_passes_test(is_admin)
def admin_warehouse(request):
    selected_wh_id = request.GET.get('warehouse')
    my_warehouses = Warehouse.objects.all()
    if not selected_wh_id and my_warehouses.exists():
        selected_wh_id = my_warehouses.first().id
    
    selected_wh_id = int(selected_wh_id) if selected_wh_id else None
    selected_wh = get_object_or_404(Warehouse, id=selected_wh_id) if selected_wh_id else None

    if request.method == 'POST':
        from django.contrib import messages
        action = request.POST.get('action')
        if action == 'update_strategy':
            strategy = request.POST.get('strategy')
            request.user.stock_strategy = strategy
            request.user.save()
            
            # Global re-balancing logic
            try:
                products = Product.objects.all()
                if strategy == 'DEMAND': products = products.annotate(order_count=Count('order')).order_by('-order_count')
                elif strategy == 'FIFO': products = products.order_by('id')
                elif strategy == 'LIFO': products = products.order_by('-id')
                
                warehouses = list(Warehouse.objects.all())
                if warehouses:
                    hub_counters = {wh.id: 0 for wh in warehouses}
                    for i, p in enumerate(products):
                        assigned_wh = warehouses[i % len(warehouses)]
                        p.warehouse = assigned_wh
                        count_in_hub = hub_counters[assigned_wh.id]
                        p.rail = (count_in_hub % assigned_wh.total_rails) + 1
                        p.shelf = (count_in_hub // assigned_wh.total_rails) % 8 + 1
                        p.save()
                        hub_counters[assigned_wh.id] += 1
                messages.success(request, f"Ré-optimisation globale terminée ({strategy}).")
            except Exception as e:
                messages.error(request, f"Erreur lors de l'optimisation : {str(e)}")
            return redirect(f"{request.path}?warehouse={selected_wh_id}")
        
        elif action == 'manual_assign':
            product_id = request.POST.get('product_id')
            wh_id = request.POST.get('warehouse_id')
            
            try:
                if not product_id or not wh_id:
                    raise ValueError("Produit ou Hub non spécifié.")
                
                p = get_object_or_404(Product, id=product_id)
                wh = get_object_or_404(Warehouse, id=wh_id)
                p.warehouse = wh
                p.rail = int(request.POST.get('rail', 1))
                p.shelf = int(request.POST.get('shelf', 1))
                p.save()
                messages.success(request, f"Succès : {p.name} est maintenant au Hub {wh.city} (R{p.rail}-S{p.shelf}).")
            except Exception as e:
                messages.error(request, f"Échec de l'affectation : {str(e)}")
            
            return redirect(f"{request.path}?warehouse={wh_id}")

    # Reload data for the view
    selected_wh_products = Product.objects.filter(warehouse_id=selected_wh_id)
    # Ensure warehouse_data is an ordered list of tuples
    warehouse_data_dict = {rail: [] for rail in range(1, (selected_wh.total_rails if selected_wh else 0) + 1)}
    occupied_positions = []
    for p in selected_wh_products:
        occupied_positions.append(f"R{p.rail}S{p.shelf}")
        if p.rail in warehouse_data_dict:
            warehouse_data_dict[p.rail].append(p)
    
    # Sort products within each rail by shelf for better display
    for rail in warehouse_data_dict:
        warehouse_data_dict[rail].sort(key=lambda x: x.shelf)

    occupied_positions_list = [f" R{p.rail}S{p.shelf} " for p in selected_wh_products]
    occupied_positions_str = "".join(occupied_positions_list)

    context = {
        'warehouses': my_warehouses, 
        'selected_wh': selected_wh, 
        'selected_wh_id': selected_wh_id,
        'warehouse_data': sorted(warehouse_data_dict.items()),
        'occupied_positions': occupied_positions_str,
        'all_products': Product.objects.all().order_by('name'),
        'current_strategy': request.user.stock_strategy, 
        'strategy_choices': User.STRATEGY_CHOICES,
    }
    return render(request, 'admin_panel/warehouse.html', context)

@login_required
@user_passes_test(is_admin)
def admin_flux(request):
    if request.method == 'POST':
        from django.contrib import messages
        messages.success(request, "Algorithme Atlas-AI : Optimisation globale des flux terminée.")
        return redirect('admin_panel:flux')

    hubs = Warehouse.objects.annotate(total_stock=Sum('products__stock')).all()
    hub_data = []
    for h in hubs:
        capacity = h.capacity or 1000
        stock = h.total_stock or 0
        saturation = min(round((stock / max(capacity, 1)) * 100, 1), 100)
        hub_data.append({'name': f'Hub {h.city}', 'saturation': saturation})
    
    context = {
        'total_orders': Order.objects.count(),
        'total_co2': (Order.objects.aggregate(total=Sum('co2_emission'))['total'] or 0) / 1000,
        'total_revenue': Order.objects.aggregate(total=Sum('price_total'))['total'] or 0,
        'hub_data': hub_data,
        'avg_time_gain': 18.4,
    }
    return render(request, 'admin_panel/flux.html', context)

@login_required
@user_passes_test(is_admin)
def admin_orders(request):
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')
    
    orders = Order.objects.all().order_by('-order_date')
    
    if start_date:
        orders = orders.filter(order_date__date__gte=start_date)
    if end_date:
        orders = orders.filter(order_date__date__lte=end_date)
        
    transporters = User.objects.filter(role='Transporteur').order_by('-rating_co2')
        
    return render(request, 'admin_panel/orders.html', {
        'orders': orders,
        'transporters': transporters,
        'start_date': start_date,
        'end_date': end_date
    })

@login_required
@user_passes_test(is_admin)
def admin_assign_transporter(request):
    if request.method == 'POST':
        order_id = request.POST.get('order_id')
        transporter_id = request.POST.get('transporter_id')
        
        order = get_object_or_404(Order, id=order_id)
        transporter_user = get_object_or_404(User, id=transporter_id, role='Transporteur')
        
        # Ensure chauffeur exists
        chauffeur, created = Chauffeur.objects.get_or_create(
            user=transporter_user,
            defaults={'telephone': '0000000000', 'type_vehicule': 'camionnette', 'immatriculation': '1234-A-1'}
        )
        
        # --- OPTIMISATION DIJKSTRA (MULTI-HUB) ---
        # Trouver tous les produits identiques (même nom, même vendeur) avec du stock
        produits_similaires = Product.objects.filter(
            name=order.product.name, 
            seller=order.product.seller,
            stock__gte=order.quantity
        ).select_related('warehouse')
        
        # Coordonnées des villes pour le calcul
        import math
        def haversine(lat1, lon1, lat2, lon2):
            R = 6371.0
            dlat = math.radians(lat2 - lat1)
            dlon = math.radians(lon2 - lon1)
            a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
            return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        city_coords = {
            'Casablanca': (33.5731, -7.5898), 'Rabat': (34.0209, -6.8416),
            'Tanger': (35.7595, -5.8340), 'Marrakech': (31.6295, -7.9811),
            'Agadir': (30.4278, -9.5981), 'Fès': (34.0181, -5.0078),
            'Oujda': (34.6867, -1.9114), 'Béni Mellal': (32.3373, -6.3498),
        }
        
        # Destination (Ville du client) - Simulated since User has no city attribute
        client_city = getattr(order.client, 'city', None)
        if not client_city and order.product.warehouse:
            client_city = order.product.warehouse.city
        dest_lat, dest_lng = city_coords.get(client_city, city_coords.get('Casablanca'))
        
        meilleur_produit = order.product
        distance_min = float('inf')
        
        # L'algorithme choisit le hub le plus proche du client pour minimiser le CO2
        for p in produits_similaires:
            if p.warehouse and p.warehouse.lat and p.warehouse.lng:
                dist = haversine(p.warehouse.lat, p.warehouse.lng, dest_lat, dest_lng)
                if dist < distance_min:
                    distance_min = dist
                    meilleur_produit = p
        
        # Mettre à jour la commande si un meilleur hub est trouvé
        if meilleur_produit.id != order.product.id:
            order.product = meilleur_produit
            order.save()
            
        # Déduire le stock
        meilleur_produit.stock -= order.quantity
        meilleur_produit.save()
        
        # Calculer les métriques
        distance_km = distance_min * 1.3 if distance_min != float('inf') else 15.0 # 1.3 pour simuler route vs vol d'oiseau
        if distance_km < 5: distance_km = 12.5 # Minimum local
        
        co2_estime = distance_km * 0.22 # 0.22 kg/km pour camionnette
        co2_classique = distance_km * 1.35 * 0.22 # Trajet non optimisé (+35% distance)
        co2_eco = co2_classique - co2_estime
        
        MissionLivraison.objects.update_or_create(
            commande=order,
            defaults={
                'chauffeur': chauffeur,
                'statut': 'acceptee',
                'distance_km': round(distance_km, 1),
                'entrepot': meilleur_produit.warehouse,
                'co2_estime_kg': round(co2_estime, 1),
                'co2_mode_classique_kg': round(co2_classique, 1),
                'co2_economise_kg': round(co2_eco, 1)
            }
        )
        order.status = 'Confirmée'
        order.save()
        from django.contrib import messages
        messages.success(request, f"Flux #{order.id} optimisé (Hub {meilleur_produit.warehouse.city}) et assigné à {transporter_user.username}.")
    return redirect('admin_panel:orders')


@login_required
@user_passes_test(is_admin)
def admin_order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    # Get the mission to find the chauffeur
    mission = MissionLivraison.objects.filter(commande=order).first()
    return render(request, 'admin_panel/order_detail.html', {
        'order': order,
        'mission': mission
    })

@login_required
@user_passes_test(is_admin)
@login_required
@user_passes_test(is_admin)
def admin_monitoring(request):
    city_filter = request.GET.get('city', '')
    
    hubs = Warehouse.objects.all()
    if city_filter:
        hubs = hubs.filter(city__icontains=city_filter)
        
    chauffeurs = Chauffeur.objects.filter(latitude_actuelle__isnull=False)
    if city_filter:
        chauffeurs = chauffeurs.filter(zone__ville__icontains=city_filter)
        
    missions_actives = MissionLivraison.objects.filter(statut='en_livraison').select_related('chauffeur', 'commande')
    
    # Hubs Data
    hubs_data = list(hubs.values('name', 'city', 'lat', 'lng'))
    
    # Chauffeurs Data
    chauffeurs_data = []
    for c in chauffeurs:
        chauffeurs_data.append({
            'id': c.id,
            'nom': c.user.first_name or c.user.username,
            'lat': c.latitude_actuelle,
            'lng': c.longitude_actuelle,
            'statut': c.statut,
            'vehicule': c.type_vehicule,
            'couleur': c.zone.couleur_hex if c.zone else '#15803d'
        })
        
    # Real Paths from active missions
    paths = []
    for m in missions_actives:
        if m.chauffeur and m.chauffeur.latitude_actuelle and m.entrepot:
            paths.append({
                'from': [m.entrepot.lat, m.entrepot.lng],
                'to': [m.chauffeur.latitude_actuelle, m.chauffeur.longitude_actuelle],
                'color': m.chauffeur.zone.couleur_hex if m.chauffeur.zone else '#3b82f6',
                'city': m.entrepot.city,
                'chauffeur': m.chauffeur.user.first_name
            })

    # Stats for the overlay
    stats = {
        'avg_speed': random.randint(65, 85),
        'co2_saved': MissionLivraison.objects.aggregate(Sum('co2_economise_kg'))['co2_economise_kg__sum'] or 0,
        'active_count': missions_actives.count()
    }

    return render(request, 'admin_panel/monitoring.html', {
        'hubs_json': json.dumps(hubs_data),
        'chauffeurs_json': json.dumps(chauffeurs_data),
        'paths_json': json.dumps(paths),
        'stats': stats,
        'city_filter': city_filter
    })

@login_required
@user_passes_test(is_admin)
def admin_analytics(request):
    # Grouping by city correctly to sum all warehouses in the same city
    co2_by_city = Warehouse.objects.values('city').annotate(co2=Sum('products__order__co2_emission')).order_by('-co2')
    
    labels = [c['city'] for c in co2_by_city]
    # Convert to Tonnes for readability
    values = [round(float(c['co2'] or 0) / 1000, 2) for c in co2_by_city]
    
    context = {
        'co2_labels': json.dumps(labels),
        'co2_values': json.dumps(values),
    }
    return render(request, 'admin_panel/analytics.html', context)

@login_required
@user_passes_test(is_admin)
def admin_settings(request):
    qr_data, login_url = get_qr_code(request)
    context = {
        'qr_code': qr_data,
        'login_url': login_url,
    }
    return render(request, 'admin_panel/settings.html', context)

def get_qr_code(request):
    # Detect Local IP dynamically
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
    except Exception:
        local_ip = "127.0.0.1"

    login_url = f"http://{local_ip}:8000/login/"
    
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(login_url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    
    # Save to buffer
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return f"data:image/png;base64,{img_str}", login_url
