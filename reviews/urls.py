from django.urls import path
from . import views

urlpatterns = [
    # Customer endpoints
    path('my/', views.my_reviews),
    path('<int:product_id>/', views.product_reviews),
    path('<int:product_id>/create/', views.create_review),
    path('<int:product_id>/<int:review_id>/', views.update_review),
    path('<int:product_id>/<int:review_id>/delete/', views.delete_review),

    # Admin endpoints
    path('admin/', views.admin_list_reviews),
    path('admin/stats/', views.admin_review_stats),
    path('admin/<int:review_id>/moderate/', views.moderate_review),
    path('admin/<int:review_id>/delete/', views.admin_delete_review),
]