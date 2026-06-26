import django_filters
from .models import Product

class ProductFilter(django_filters.FilterSet):
    
    min_price = django_filters.NumberFilter(
        field_name='price', lookup_expr='gte'
    )
    max_price = django_filters.NumberFilter(
        field_name='price', lookup_expr='lte'
    )

    # فلترة بالتوفر
    in_stock = django_filters.BooleanFilter(
        method='filter_in_stock'
    )

    # فلترة بالماركة عن طريق الاسم بدل الـ ID
    brand_name = django_filters.CharFilter(
        field_name='brand__name', lookup_expr='icontains'
    )

    # فلترة بالفئة عن طريق الاسم بدل الـ ID
    category_name = django_filters.CharFilter(
        field_name='category__name', lookup_expr='icontains'
    )

    class Meta:
        model = Product
        fields = ['brand', 'category', 'min_price', 'max_price', 'in_stock']

    def filter_in_stock(self, queryset, name, value):
        if value:
            return queryset.filter(stock_qty__gt=0)
        return queryset.filter(stock_qty=0)