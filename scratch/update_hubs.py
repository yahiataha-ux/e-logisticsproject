import os
import django
import sys

sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'atlas_logistics.settings')
django.setup()

from apps.logistics_core.models import Warehouse

def update_hub_capacities():
    hubs_config = {
        "Casablanca": 24,
        "Tanger": 18,
        "Marrakech": 16,
        "Rabat": 14,
        "Agadir": 12,
        "Fès": 10,
        "Oujda": 8
    }
    
    hubs = Warehouse.objects.all()
    print(f"Updating {hubs.count()} hubs...")
    
    for h in hubs:
        new_rails = hubs_config.get(h.city, 12)
        h.total_rails = new_rails
        h.save()
        print(f"Updated {h.city}: {h.total_rails} rails")

if __name__ == '__main__':
    update_hub_capacities()
