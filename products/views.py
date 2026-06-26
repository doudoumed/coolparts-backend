from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import Category, Brand, Product
from .serializers import CategorySerializer, BrandSerializer, ProductSerializer
from .filters import ProductFilter
from config.permissions import IsAdminOrReadOnly

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrReadOnly]

class BrandViewSet(viewsets.ModelViewSet):
    queryset = Brand.objects.all()
    serializer_class = BrandSerializer
    permission_classes = [IsAdminOrReadOnly]

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.filter(is_active=True).select_related('brand', 'category')
    serializer_class = ProductSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter      # ← جديد
    ]
    filterset_class = ProductFilter  # ← بدل filterset_fields
    search_fields = ['name', 'description', 'brand__name', 'category__name']
    ordering_fields = ['price', 'created_at', 'name', 'stock_qty']
    ordering = ['-created_at']       # ← الترتيب الافتراضي: الأحدث أولاً

    @action(detail=False, methods=['get'], url_path='in-stock')
    def in_stock(self, request):
        """endpoint سريع للمنتجات المتوفرة فقط"""
        products = self.get_queryset().filter(stock_qty__gt=0)
        serializer = self.get_serializer(products, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='low-stock')
    def low_stock(self, request):
        """للأدمن: منتجات على وشك النفاد (أقل من 5)"""
        if not request.user.is_staff:
            return Response({'error': 'Admin only'}, status=403)
        products = self.get_queryset().filter(stock_qty__lte=5)
        serializer = self.get_serializer(products, many=True)
        return Response(serializer.data)