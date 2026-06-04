from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from apps.logistics_core.models import Product, Warehouse
from apps.authentication.models import User
from apps.client.models import Order
from django.db.models import Sum, Count
from django.contrib import messages
from django.http import HttpResponse
import pandas as pd
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from apps.transporter.models import MissionLivraison, Chauffeur
from apps.authentication.decorators import role_required
from django.utils import timezone
import random

@login_required
@role_required('Entreprise')
def enterprise_dashboard(request):
    user = request.user
    my_products = Product.objects.filter(seller=user)
    my_orders = Order.objects.filter(product__seller=user)
    total_sales = my_orders.aggregate(total=Sum('price_total'))['total'] or 0
    total_co2 = (my_orders.aggregate(total=Sum('co2_emission'))['total'] or 0) / 1000
    context = {
        'products': my_products,
        'orders': my_orders.order_by('-order_date')[:10],
        'total_sales': total_sales,
        'total_co2': total_co2,
        'stock_alerts': my_products.filter(stock__lt=20).count(),
    }
    return render(request, 'enterprise/dashboard.html', context)

@login_required
@role_required('Entreprise')
def product_management(request):
    user = request.user
    query_p = request.GET.get('product')
    query_wh = request.GET.get('warehouse')
    
    # Base query
    all_my_products = Product.objects.filter(seller=user).select_related('warehouse')
    
    if query_p:
        all_my_products = all_my_products.filter(name__icontains=query_p)
    if query_wh:
        all_my_products = all_my_products.filter(warehouse_id=query_wh)

    # Grouping
    inventory = {}
    for p in all_my_products:
        if p.name not in inventory:
            inventory[p.name] = {
                'details': p,
                'distribution': []
            }
        inventory[p.name]['distribution'].append(p)
        
    warehouses = Warehouse.objects.all()
    # For filters
    my_product_names = Product.objects.filter(seller=user).values_list('name', flat=True).distinct()
    
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'replenish':
            product_id = request.POST.get('product_id')
            amount = int(request.POST.get('amount', 0))
            p = get_object_or_404(Product, id=product_id, seller=user)
            p.stock += amount
            p.save()
            messages.success(request, f"Stock de {p.name} réapprovisionné au Hub {p.warehouse.city} (+{amount}).")
        
        elif action == 'fast_deploy':
            # Add existing product to a new hub
            name = request.POST.get('name')
            wh_id = request.POST.get('warehouse_id')
            amount = int(request.POST.get('amount', 100))
            
            # Get template info from an existing product of the same name
            template = Product.objects.filter(seller=user, name=name).first()
            if template:
                wh = get_object_or_404(Warehouse, id=wh_id)
                Product.objects.create(
                    name=name, category=template.category, price=template.price,
                    stock=amount, seller=user, warehouse=wh, co2_impact=template.co2_impact,
                    rail=1, shelf=1, image=template.image
                )
                messages.success(request, f"{name} déployé avec succès au Hub {wh.city}.")
        
        return redirect('enterprise:products')

    return render(request, 'enterprise/products.html', {
        'inventory': inventory,
        'warehouses': warehouses,
        'my_product_names': my_product_names,
        'query_p': query_p,
        'query_wh': query_wh
    })

@login_required
@role_required('Entreprise')
def add_product(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        price = float(request.POST.get('price', 0))
        stock = int(request.POST.get('stock', 0))
        category = request.POST.get('category')
        warehouse_id = request.POST.get('warehouse_id')
        warehouse = get_object_or_404(Warehouse, id=warehouse_id)
        
        image = request.FILES.get('image')
        
        Product.objects.create(
            name=name, price=price, stock=stock, category=category,
            seller=request.user, warehouse=warehouse, co2_impact=round(random.uniform(0.1, 1.5), 2),
            rail=1, shelf=1, image=image
        )
        messages.success(request, f"Produit {name} enregistré pour dépôt au Hub {warehouse.city}.")
    return redirect('enterprise:products')

@login_required
@role_required('Entreprise')
def delete_product(request, product_id):
    product = get_object_or_404(Product, id=product_id, seller=request.user)
    if request.method == 'POST':
        product.delete()
        messages.warning(request, "Produit supprimé du catalogue.")
    return redirect('enterprise:products')

@login_required
@role_required('Entreprise')
def order_management(request):
    my_orders = Order.objects.filter(product__seller=request.user).select_related('client', 'product').prefetch_related('missionlivraison').order_by('-order_date')
    transporters = User.objects.filter(role='Transporteur').order_by('-rating_co2')
    return render(request, 'enterprise/orders.html', {
        'orders': my_orders,
        'transporters': transporters
    })

@login_required
@role_required('Entreprise')
def delivery_note(request, order_id):
    order = get_object_or_404(Order, id=order_id, product__seller=request.user)
    mission = MissionLivraison.objects.filter(commande=order).first()
    return render(request, 'enterprise/delivery_note.html', {
        'order': order,
        'mission': mission,
        'date': timezone.now()
    })

@login_required
@role_required('Entreprise')
def export_delivery_note_pdf(request, order_id):
    order = get_object_or_404(Order, id=order_id, product__seller=request.user)
    mission = MissionLivraison.objects.filter(commande=order).first()
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Bon_Sortie_ATL_{order.id:05d}.pdf"'
    
    p = canvas.Canvas(response, pagesize=A4)
    width, height = A4
    
    # Header
    p.setFillColor(colors.HexColor("#0f172a"))
    p.rect(0, height-4*cm, width, 4*cm, fill=1)
    p.setFillColor(colors.white)
    p.setFont("Helvetica-Bold", 24)
    p.drawString(1*cm, height-2*cm, "ATLAS LOGISTICS")
    p.setFont("Helvetica", 10)
    p.drawString(1*cm, height-2.8*cm, "Réseau Intelligent de Distribution - Casablanca, Maroc")
    
    p.setFont("Helvetica-Bold", 18)
    p.drawRightString(width-1*cm, height-2*cm, "BON DE SORTIE")
    p.setFont("Helvetica", 12)
    p.drawRightString(width-1*cm, height-2.8*cm, f"N° #ATL-{order.id:05d}")
    
    # Content
    p.setFillColor(colors.black)
    y = height - 6*cm
    
    # Stakeholders
    p.setFont("Helvetica-Bold", 12)
    p.drawString(1*cm, y, "Émetteur (PME) :")
    p.drawString(width/2 + 1*cm, y, "Destinataire (Client) :")
    
    y -= 0.8*cm
    p.setFont("Helvetica", 11)
    p.drawString(1.5*cm, y, f"{order.product.seller.company_name or order.product.seller.username}")
    p.drawString(width/2 + 1.5*cm, y, f"{order.client.get_full_name() or order.client.username}")
    
    y -= 2*cm
    # Table Header
    p.setFont("Helvetica-Bold", 11)
    p.setFillColor(colors.HexColor("#f1f5f9"))
    p.rect(1*cm, y-0.2*cm, width-2*cm, 0.8*cm, fill=1, stroke=0)
    p.setFillColor(colors.black)
    p.drawString(1.2*cm, y, "Désignation Produit")
    p.drawCentredString(width/2 + 1*cm, y, "Quantité")
    p.drawCentredString(width/2 + 4*cm, y, "Origine")
    p.drawRightString(width-1.2*cm, y, "Impact CO2")
    
    y -= 1*cm
    p.setFont("Helvetica", 10)
    p.drawString(1.2*cm, y, f"{order.product.name}")
    p.drawCentredString(width/2 + 1*cm, y, f"{order.quantity}")
    p.drawCentredString(width/2 + 4*cm, y, f"{order.product.warehouse.city}")
    p.drawRightString(width-1.2*cm, y, f"{order.co2_emission:.2f} kg")
    
    # Logistics Info
    y -= 3*cm
    p.setFont("Helvetica-Bold", 12)
    p.drawString(1*cm, y, "Détails Transport :")
    y -= 0.8*cm
    p.setFont("Helvetica", 11)
    p.drawString(1.5*cm, y, f"Chauffeur : {mission.chauffeur.user.username if mission else 'En attente'}")
    y -= 0.5*cm
    p.drawString(1.5*cm, y, f"Véhicule : {mission.chauffeur.get_type_vehicule_display() if mission else '---'}")
    y -= 0.5*cm
    p.drawString(1.5*cm, y, f"Matricule : {mission.chauffeur.immatriculation if mission else '---'}")
    
    # Footer
    p.setFont("Helvetica-Oblique", 8)
    p.drawCentredString(width/2, 2*cm, "Document généré par Atlas AI Infrastructure - Casablanca")
    
    p.showPage()
    p.save()
    return response





@login_required
@role_required('Entreprise')
def export_orders_excel(request):
    orders = Order.objects.filter(product__seller=request.user).select_related('client', 'product')
    data = []
    for o in orders:
        data.append({'Flux ID': f'#ATL-{o.id:05d}', 'Client': o.client.company_name or o.client.username,
                     'Produit': o.product.name, 'Quantité': o.quantity, 'Valeur (MAD)': o.price_total,
                     'Impact CO2 (T)': o.co2_emission / 1000, 'Statut': o.status, 'Date': o.order_date.strftime('%d/%m/%Y %H:%M')})
    df = pd.DataFrame(data)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Commandes Atlas')
    output.seek(0)
    response = HttpResponse(output.read(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=commandes_atlas.xlsx'
    return response

@login_required
@role_required('Entreprise')
def export_carbon_pdf(request):
    user = request.user
    products = Product.objects.filter(seller=user)
    total_co2_potential = products.aggregate(Sum('co2_impact'))['co2_impact__sum'] or 0
    saving_percentage = 0.32
    co2_saved = total_co2_potential * saving_percentage
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Certificat_Carbone_{user.username}.pdf"'
    p = canvas.Canvas(response, pagesize=A4)
    width, height = A4
    p.setFillColor(colors.HexColor("#064e3b"))
    p.rect(0, height-4*cm, width, 4*cm, fill=1)
    p.setFillColor(colors.white)
    p.setFont("Helvetica-Bold", 24)
    p.drawString(2*cm, height-2*cm, "Certificat de Durabilité Atlas")
    p.setFont("Helvetica", 12)
    p.drawString(2*cm, height-2.8*cm, f"Émis pour : {user.username.upper()} LOGISTICS")
    p.setFillColor(colors.black)
    p.setFont("Helvetica-Bold", 16)
    p.drawString(2*cm, height-6*cm, "Rapport d'Impact Environnemental")
    p.setFont("Helvetica", 11)
    lines = [f"Total CO2 Économisé : {co2_saved/1000:.2f} T", f"Réduction Moyenne : {saving_percentage*100:.1f}%", f"Carburant Évité : {(co2_saved)*0.38:.1f} L"]
    y = height-7*cm
    for line in lines:
        p.drawString(2*cm, y, line)
        y -= 0.6*cm
    p.showPage()
    p.save()
    return response


@login_required
@role_required('Entreprise')
def carbon_reports(request):
    user = request.user
    my_orders = Order.objects.filter(product__seller=user)
    my_products = Product.objects.filter(seller=user)
    total_co2_real = (my_orders.aggregate(total=Sum('co2_emission'))['total'] or 0) / 1000
    total_co2_potential = (my_products.aggregate(total=Sum('co2_impact'))['total'] or 0) / 1000
    # Économie carbone : 32% de l'émission totale (standard = réelle + économisée)
    # co2_saved = 0.32 * (total_co2_real + co2_saved) => co2_saved = total_co2_real * (0.32 / 0.68)
    co2_saved_kg = total_co2_real * 1000 * (32 / 68)
    # Évolution hebdomadaire simulée sur base réelle (en kg)
    import random
    base = max((total_co2_real * 1000) / 8, 50)
    weekly_data = [round(base * (1 + random.uniform(-0.15, 0.15) + (7-i)*0.05), 1) for i in range(8)]
    context = {
        'total_co2_real': total_co2_real,
        'co2_saved_kg': co2_saved_kg,
        'co2_saved_tonnes': round(co2_saved_kg / 1000, 2),
        'reduction_pct': 32,
        'fuel_saved': round(co2_saved_kg * 0.38, 1),
        'weekly_data': weekly_data,
        'total_orders': my_orders.count(),
    }
    return render(request, 'enterprise/carbon.html', context)
