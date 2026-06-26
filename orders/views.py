from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Order, OrderItem
from .serializers import OrderSerializer
from cart.models import Cart, CartItem

def get_cart(request):
    if request.user.is_authenticated:
        cart = Cart.objects.filter(user=request.user).first()
    else:
        session_key = request.session.session_key
        cart = Cart.objects.filter(session_key=session_key).first()
    return cart

@api_view(['POST'])
def create_order(request):
    # Step 1: جيب السلة الحالية
    cart = get_cart(request)

    if not cart:
        return Response(
            {'error': 'No cart found'},
            status=status.HTTP_400_BAD_REQUEST
        )

    cart_items = cart.items.select_related('product').all()

    if not cart_items.exists():
        return Response(
            {'error': 'Your cart is empty'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Step 2: تحقق من البيانات المرسلة (الاسم، الهاتف، العنوان)
    serializer = OrderSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # Step 3: تحقق من المخزون قبل ما تكمل
    for item in cart_items:
        if item.product.stock_qty < item.quantity:
            return Response(
                {'error': f'Not enough stock for {item.product.name}. Available: {item.product.stock_qty}'},
                status=status.HTTP_400_BAD_REQUEST
            )

    # Step 4: احسب المجموع الكلي
    total = sum(item.product.price * item.quantity for item in cart_items)

    # Step 5: أنشئ الطلب
    order = Order.objects.create(
        user=request.user if request.user.is_authenticated else None,
        full_name=serializer.validated_data['full_name'],
        phone=serializer.validated_data['phone'],
        address=serializer.validated_data['address'],
        total=total
    )

    # Step 6: أنشئ عناصر الطلب (snapshot من السلة)
    for item in cart_items:
        OrderItem.objects.create(
            order=order,
            product=item.product,
            product_name=item.product.name,
            price=item.product.price,
            quantity=item.quantity
        )
        # Step 7: نقّص المخزون
        item.product.stock_qty -= item.quantity
        item.product.save()

    # Step 8: فرّغ السلة بعد الطلب
    cart.items.all().delete()

    return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
def my_orders(request):
    if not request.user.is_authenticated:
        return Response(
            {'error': 'Login required'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return Response(OrderSerializer(orders, many=True).data)


@api_view(['GET'])
def order_detail(request, order_id):
    try:
        if request.user.is_authenticated:
            order = Order.objects.get(id=order_id, user=request.user)
        else:
            return Response({'error': 'Login required'}, status=status.HTTP_401_UNAUTHORIZED)
    except Order.DoesNotExist:
        return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)

    return Response(OrderSerializer(order).data)