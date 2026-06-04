import os
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "atlas_logistics.settings")
django.setup()
from apps.authentication.models import User
from apps.client.models import Order
from apps.logistics_core.models import Product

print("Checking Order Distribution:")
for user in User.objects.filter(role='Entreprise'):
    count = Order.objects.filter(product__seller=user).count()
    print(f"Enterprise {user.username}: {count} orders")

print("\nTotal Orders:", Order.objects.count())
