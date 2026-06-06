from django.urls import path
from apps.client import views

from django.shortcuts import redirect

urlpatterns = [
    path('', lambda request: redirect('client:marketplace')),
    path('marketplace/', views.marketplace_view, name='marketplace'),
    path('impact-eco/', views.impact_eco_view, name='impact_eco'),
    path('orders/', views.orders_view, name='orders'),
    path('tracking/<int:order_id>/', views.tracking_view, name='tracking'),
    path('order/form/<int:product_id>/', views.order_form_view, name='order_form'),
]
