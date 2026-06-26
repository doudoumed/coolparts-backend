from django.contrib import admin
from .models import Order, OrderItem

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0

class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'full_name', 'status', 'total', 'created_at']
    list_filter = ['status']
    inlines = [OrderItemInline]

admin.site.register(Order, OrderAdmin)