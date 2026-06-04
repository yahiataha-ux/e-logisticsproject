import os
import django
import random
import sys

sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'atlas_logistics.settings')
django.setup()

from apps.authentication.models import User

def fix_ratings():
    transporters = User.objects.filter(role='Transporteur')
    print(f"Updating {transporters.count()} transporters...")
    
    for t in transporters:
        t.rating_co2 = round(random.uniform(3.8, 4.9), 1)
        t.rating_time = round(random.uniform(4.0, 5.0), 1)
        t.rating_price = round(random.uniform(3.2, 4.7), 1)
        t.save()
        print(f"Updated {t.username}: CO2={t.rating_co2}, Time={t.rating_time}, Price={t.rating_price}")

    print("Done!")

if __name__ == '__main__':
    fix_ratings()
