import os
import django
import sys

sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'atlas_logistics.settings')
django.setup()

from apps.authentication.models import User
from apps.logistics_core.models import Product, Warehouse
from django.db.models import Count

def optimize_all():
    enterprises = User.objects.filter(role='Entreprise')
    warehouses = list(Warehouse.objects.all())
    
    if not warehouses:
        print("No warehouses found.")
        return

    for ent in enterprises:
        print(f"Optimizing {ent.username}...")
        products = Product.objects.filter(seller=ent).annotate(order_count=Count('order')).order_by('-order_count')
        
        hub_counters = {wh.id: 0 for wh in warehouses}
        
        for i, p in enumerate(products):
            assigned_wh = warehouses[i % len(warehouses)]
            p.warehouse = assigned_wh
            
            count_in_hub = hub_counters[assigned_wh.id]
            p.rail = (count_in_hub % assigned_wh.total_rails) + 1
            p.shelf = (count_in_hub // assigned_wh.total_rails) % 8 + 1
            p.save()
            
            hub_counters[assigned_wh.id] += 1
            
    print("Global optimization complete for all enterprises.")

if __name__ == '__main__':
    optimize_all()
