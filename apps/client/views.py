import random
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from apps.logistics_core.models import Product, Warehouse
from apps.transporter.models import MissionLivraison, Chauffeur
from apps.authentication.models import User
from .models import Order
from django.contrib import messages
from django.utils import timezone

@login_required
def marketplace_view(request):
    products_list = list(Product.objects.all())
    
    if products_list:
        max_price = max(p.price for p in products_list) or 1
        max_co2 = max(p.co2_impact for p in products_list) or 1
        
        for p in products_list:
            # Score: 0 is perfect (low price, low co2), 1 is worst
            price_score = p.price / max_price
            co2_score = p.co2_impact / max_co2
            p.performance_score = (price_score + co2_score) / 2
            # For display: 100 - (score * 100) to have a "Performance Index"
            p.performance_index = round(100 - (p.performance_score * 100))
            
            # Determine color class
            if p.performance_index >= 80:
                p.impact_color = "emerald"
            elif p.performance_index >= 50:
                p.impact_color = "amber"
            else:
                p.impact_color = "rose"
        
        # Sort by performance_score (ascending = better)
        products_list.sort(key=lambda x: x.performance_score)
    
    return render(request, 'client/marketplace.html', {'products': products_list})

@login_required
def impact_eco_view(request):
    orders = Order.objects.filter(client=request.user)
    total_co2 = sum(o.co2_emission for o in orders) / 1000
    
    # Simple simulation: Standard delivery would be 3x more CO2
    co2_saved = total_co2 * 2.5 
    
    # Top eco products
    eco_products = Product.objects.order_by('co2_impact')[:5]
    
    context = {
        'total_co2': total_co2,
        'co2_saved': co2_saved,
        'eco_products': eco_products,
        'total_orders': orders.count()
    }
    return render(request, 'client/impact_eco.html', context)

@login_required
def orders_view(request):
    orders = Order.objects.filter(client=request.user).select_related('product').order_by('-order_date')
    return render(request, 'client/orders.html', {'orders': orders})

@login_required
def tracking_view(request, order_id):
    order = get_object_or_404(Order, id=order_id, client=request.user)
    try:
        mission = order.missionlivraison
    except:
        mission = None
    
    # City to Coords Mapping for Morocco
    CITY_COORDS = {
        'Casablanca': [33.5731, -7.5898],
        'Rabat': [34.0209, -6.8416],
        'Tanger': [35.7595, -5.8340],
        'Marrakech': [31.6295, -7.9811],
        'Agadir': [30.4278, -9.5981],
        'Fès': [34.0181, -5.0078],
        'Oujda': [34.6867, -1.9114],
        'Dakhla': [23.6848, -15.9579]
    }
    
    origin = [order.product.warehouse.lat, order.product.warehouse.lng]
    destination = CITY_COORDS.get('Casablanca', [33.5731, -7.5898]) # fallback
    
    # Current Vehicle Location (Simulated if not set)
    vehicle_loc = origin # Default
    if mission and mission.chauffeur:
        vehicle_loc = [mission.chauffeur.latitude_actuelle or origin[0], mission.chauffeur.longitude_actuelle or origin[1]]
    
    # Suggestions logic: Find transporters with active vehicles
    suggested_transporters = Chauffeur.objects.filter(statut='disponible')[:3]
    
    context = {
        'order': order,
        'mission': mission,
        'suggested_transporters': suggested_transporters,
        'origin_coords': origin,
        'dest_coords': destination,
        'vehicle_coords': vehicle_loc
    }
    return render(request, 'client/tracking.html', context)

@login_required
def place_order(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if product.stock > 0:
        order = Order.objects.create(
            client=request.user,
            product=product,
            status='Confirmée',
            price_total=product.price,
            co2_emission=product.co2_impact,
            order_date=timezone.now()
        )
        product.stock -= 1
        product.save()
        
        MissionLivraison.objects.create(
            commande=order,
            statut='assignee',
            distance_km=15.0,
            co2_estime_kg=product.co2_impact,
            entrepot=product.warehouse
        )
        
        messages.success(request, f"Félicitations ! Votre commande de {product.name} est validée. Un transporteur sera bientôt assigné.")
        return redirect('client:orders')
    else:
        messages.error(request, "Désolé, ce produit est en rupture de stock.")
        return redirect('client:marketplace')
