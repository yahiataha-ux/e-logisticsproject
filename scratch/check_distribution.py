import os
import django
import sys

sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'atlas_logistics.settings')
django.setup()

from apps.authentication.models import User
from apps.logistics_core.models import Product, Warehouse
from django.db.models import Count

def check_products():
    enterprises = User.objects.filter(role='Entreprise')
    hubs = Warehouse.objects.all()
    
    print(f"Total Enterprises: {enterprises.count()}")
    print(f"Total Hubs: {hubs.count()}")
    print(f"Total Products: {Product.objects.count()}")
    
    for ent in enterprises:
        print(f"\nEnterprise: {ent.username}")
        prods = Product.objects.filter(seller=ent)
        print(f"  Total products: {prods.count()}")
        dist = prods.values('warehouse__city').annotate(count=Count('id'))
        for d in dist:
            print(f"  - {d['warehouse__city']}: {d['count']} products")

if __name__ == '__main__':
    check_products()
