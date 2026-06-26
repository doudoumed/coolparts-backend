from django.urls import path
from . import views

urlpatterns = [
    path('', views.view_cart),
    path('add/', views.add_to_cart),
    path('clear/', views.clear_cart),
    path('items/<int:item_id>/', views.update_cart_item),
    path('items/<int:item_id>/remove/', views.remove_cart_item),
]