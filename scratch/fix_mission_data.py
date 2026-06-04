import os
import django
import random
import sys

# Setup Django
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'atlas_logistics.settings')
django.setup()

from apps.transporter.models import Mission

def fix_missions():
    cities = ['Casablanca', 'Rabat', 'Marrakech', 'Tanger', 'Agadir', 'Fès', 'Oujda']
    vehicles = ['Van Mercedes Sprinter', 'Camion Volvo FH16', 'Drone S-400', 'Triporteur Electrique']
    
    missions = Mission.objects.filter(destination_city__isnull=True) | Mission.objects.filter(suggested_vehicle__isnull=True)
    count = missions.count()
    
    for m in missions:
        if not m.destination_city:
            m.destination_city = random.choice(cities)
        if not m.suggested_vehicle:
            # Logic similar to seed
            if m.distance < 50:
                m.suggested_vehicle = 'Triporteur Electrique'
            elif m.distance > 500:
                m.suggested_vehicle = 'Camion Volvo FH16'
            else:
                m.suggested_vehicle = 'Van Mercedes Sprinter'
        m.save()
        
    print(f"Fixed {count} missions with missing destination or vehicle.")

if __name__ == '__main__':
    fix_missions()
