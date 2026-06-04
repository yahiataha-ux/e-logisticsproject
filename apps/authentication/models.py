from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    ROLE_CHOICES = (
        ('Admin', 'Admin'),
        ('Entreprise', 'Entreprise'),
        ('Transporteur', 'Transporteur'),
        ('Client', 'Client'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='Client')
    company_name = models.CharField(max_length=255, blank=True, null=True)
    last_activity = models.DateTimeField(null=True, blank=True)
    last_ip = models.GenericIPAddressField(null=True, blank=True)
    
    STRATEGY_CHOICES = (
        ('DEMAND', 'Proximité Demande'),
        ('FIFO', 'FIFO'),
        ('LIFO', 'LIFO'),
        ('SPT', 'SPT (Shortest Processing)'),
        ('LPT', 'LPT (Longest Processing)'),
    )
    stock_strategy = models.CharField(max_length=10, choices=STRATEGY_CHOICES, default='DEMAND')
    
    # Transporter performance metrics
    rating_co2 = models.FloatField(default=0.0)
    rating_time = models.FloatField(default=0.0)
    rating_price = models.FloatField(default=0.0)

    def is_online(self):
        if self.last_activity:
            from django.utils import timezone
            return (timezone.now() - self.last_activity).total_seconds() < 300  # 5 minutes
        return False

    def save(self, *args, **kwargs):
        if self.role == 'Admin':
            self.is_staff = True
            self.is_superuser = True
        super().save(*args, **kwargs)

    def __str__(self):
        return self.username
