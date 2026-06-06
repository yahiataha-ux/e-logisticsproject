import random
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from apps.logistics_core.models import Product, Warehouse
from apps.transporter.models import MissionLivraison, Chauffeur
from apps.authentication.models import User
from .models import Order, MOROCCAN_CITIES
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
        'Meknès': [33.8935, -5.5473],
        'Kénitra': [34.2541, -6.5894],
        'Tétouan': [35.5785, -5.3684],
        'Dakhla': [23.6848, -15.9579],
        'Laâyoune': [27.1536, -13.2033],
    }
    
    origin = [order.product.warehouse.lat, order.product.warehouse.lng]
    # Use the real delivery address from the order
    destination = CITY_COORDS.get(order.delivery_address, [33.5731, -7.5898])
    
    # Current Vehicle Location (Simulated if not set)
    vehicle_loc = origin  # Default
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
        'vehicle_coords': vehicle_loc,
    }
    return render(request, 'client/tracking.html', context)

@login_required
def order_form_view(request, product_id):
    """Show the order form where the client enters quantity, delivery city, and notes."""
    product = get_object_or_404(Product, id=product_id)
    
    if product.stock <= 0:
        messages.error(request, "Désolé, ce produit est en rupture de stock.")
        return redirect('client:marketplace')
    
    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))
        delivery_address = request.POST.get('delivery_address', 'Casablanca')
        delivery_notes = request.POST.get('delivery_notes', '')
        
        # Validate quantity
        if quantity < 1:
            quantity = 1
        if quantity > product.stock:
            quantity = product.stock
        
        # Calculate totals
        price_total = product.price * quantity
        co2_total = product.co2_impact * quantity
        
        # Create the order
        order = Order.objects.create(
            client=request.user,
            product=product,
            status='Confirmée',
            price_total=price_total,
            co2_emission=co2_total,
            quantity=quantity,
            delivery_address=delivery_address,
            delivery_notes=delivery_notes,
            order_date=timezone.now()
        )
        
        # Update stock
        product.stock -= quantity
        product.save()
        
        # Create the mission
        MissionLivraison.objects.create(
            commande=order,
            statut='assignee',
            distance_km=15.0,
            co2_estime_kg=co2_total,
            entrepot=product.warehouse
        )
        
        messages.success(request, f"🎉 Votre commande de {quantity}x {product.name} à destination de {delivery_address} est confirmée ! Un transporteur sera bientôt assigné.")
        return redirect('client:orders')
    
    context = {
        'product': product,
        'cities': MOROCCAN_CITIES,
        'max_quantity': product.stock,
    }
    return render(request, 'client/order_form.html', context)
