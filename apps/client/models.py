from django.db import models
from apps.authentication.models import User
from apps.logistics_core.models import Product

class Order(models.Model):
    STATUS_CHOICES = (
        ('En attente', 'En attente'),
        ('Confirmée', 'Confirmée'),
        ('En livraison', 'En livraison'),
        ('Livrée', 'Livrée'),
    )
    client = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders', limit_choices_to={'role': 'Client'})
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='order')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='En attente')
    order_date = models.DateTimeField(auto_now_add=True)
    co2_emission = models.FloatField()
    price_total = models.FloatField()
    quantity = models.IntegerField(default=1)
    deadline = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Order {self.id} - {self.client.username}"
