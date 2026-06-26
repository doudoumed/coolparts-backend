from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Order, OrderItem
from .serializers import OrderSerializer
from cart.models import Cart
from config.permissions import IsOwnerOrAdmin

def get_cart(request):
    if request.user.is_authenticated:
        cart = Cart.objects.filter(user=request.user).first()
    else:
        session_key = request.session.session_key
        cart = Cart.objects.filter(session_key=session_key).first()
    return cart

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_order(request):
    cart = get_cart(request)

    if not cart:
        return Response({'error': 'No cart found'}, status=status.HTTP_400_BAD_REQUEST)

    cart_items = cart.items.select_related('product').all()

    if not cart_items.exists():
        return Response({'error': 'Your cart is empty'}, status=status.HTTP_400_BAD_REQUEST)

    serializer = OrderSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    for item in cart_items:
        if item.product.stock_qty < item.quantity:
            return Response(
                {'error': f'Not enough stock for {item.product.name}. Available: {item.product.stock_qty}'},
                status=status.HTTP_400_BAD_REQUEST
            )

    total = sum(item.product.price * item.quantity for item in cart_items)

    order = Order.objects.create(
        user=request.user,
        full_name=serializer.validated_data['full_name'],
        phone=serializer.validated_data['phone'],
        address=serializer.validated_data['address'],
        total=total
    )

    for item in cart_items:
        OrderItem.objects.create(
            order=order,
            product=item.product,
            product_name=item.product.name,
            price=item.product.price,
            quantity=item.quantity
        )
        item.product.stock_qty -= item.quantity
        item.product.save()

    cart.items.all().delete()

    return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_orders(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return Response(OrderSerializer(orders, many=True).data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def order_detail(request, order_id):
    try:
        order = Order.objects.get(id=order_id)
    except Order.DoesNotExist:
        return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)

    # صاحب الطلب أو الـ Admin فقط
    if order.user != request.user and not request.user.is_staff:
        return Response({'error': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)

    return Response(OrderSerializer(order).data)

# للـ Admin فقط: عرض كل الطلبات
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def all_orders(request):
    if not request.user.is_staff:
        return Response({'error': 'Admin only'}, status=status.HTTP_403_FORBIDDEN)
    orders = Order.objects.all().order_by('-created_at')
    return Response(OrderSerializer(orders, many=True).data)