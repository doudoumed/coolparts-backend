from django.urls import path
from . import views

urlpatterns = [
    path('my/', views.my_reviews),
    path('<int:product_id>/', views.product_reviews),
    path('<int:product_id>/create/', views.create_review),
    path('<int:product_id>/<int:review_id>/', views.update_review),
    path('<int:product_id>/<int:review_id>/delete/', views.delete_review),
]