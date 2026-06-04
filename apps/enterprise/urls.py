from django.urls import path
from apps.enterprise import views

from django.shortcuts import redirect

urlpatterns = [
    path('', lambda request: redirect('enterprise:dashboard')),
    path('dashboard/', views.enterprise_dashboard, name='dashboard'),
    path('products/', views.product_management, name='products'),
    path('products/add/', views.add_product, name='add_product'),
    path('products/delete/<int:product_id>/', views.delete_product, name='delete_product'),
    path('orders/', views.order_management, name='orders'),
    path('orders/delivery-note/<int:order_id>/', views.delivery_note, name='delivery_note'),
    path('orders/delivery-note/<int:order_id>/pdf/', views.export_delivery_note_pdf, name='export_delivery_note_pdf'),
    path('orders/export/', views.export_orders_excel, name='export_orders'),
    path('carbon/', views.carbon_reports, name='carbon'),
    path('carbon/export/', views.export_carbon_pdf, name='export_carbon'),
]
