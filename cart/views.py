from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Cart, CartItem
from .serializers import CartSerializer
from products.models import Product

def get_or_create_cart(request):
    if request.user.is_authenticated:
        # جيب سلة المستخدم أو أنشئ وحدة جديدة
        cart, _ = Cart.objects.get_or_create(user=request.user)

        # لو عنده سلة session قديمة (قبل ما يسجّل دخول)، ادمجها
        if request.session.session_key:
            session_cart = Cart.objects.filter(
                session_key=request.session.session_key
            ).first()

            if session_cart:
                # انقل كل عناصر السلة القديمة للسلة الجديدة
                for item in session_cart.items.all():
                    existing = cart.items.filter(product=item.product).first()
                    if existing:
                        existing.quantity += item.quantity
                        existing.save()
                    else:
                        item.cart = cart
                        item.save()
                # احذف السلة القديمة
                session_cart.delete()

    else:
        if not request.session.session_key:
            request.session.create()
        cart, _ = Cart.objects.get_or_create(
            session_key=request.session.session_key
        )
    return cart


@api_view(['GET'])
def view_cart(request):
    cart = get_or_create_cart(request)
    return Response(CartSerializer(cart).data)


@api_view(['POST'])
def add_to_cart(request):
    cart = get_or_create_cart(request)
    product_id = request.data.get('product_id')
    quantity = int(request.data.get('quantity', 1))

    try:
        product = Product.objects.get(id=product_id, is_active=True)
    except Product.DoesNotExist:
        return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)

    # تحقق من المخزون
    if product.stock_qty < quantity:
        return Response(
            {'error': f'Only {product.stock_qty} items available'},
            status=status.HTTP_400_BAD_REQUEST
        )

    item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    if not created:
        item.quantity += quantity
    else:
        item.quantity = quantity
    item.save()

    return Response(CartSerializer(cart).data, status=status.HTTP_201_CREATED)


@api_view(['PUT'])
def update_cart_item(request, item_id):
    cart = get_or_create_cart(request)
    try:
        item = CartItem.objects.get(id=item_id, cart=cart)
    except CartItem.DoesNotExist:
        return Response({'error': 'Item not found'}, status=status.HTTP_404_NOT_FOUND)

    quantity = int(request.data.get('quantity', item.quantity))

    # تحقق من المخزون
    if item.product.stock_qty < quantity:
        return Response(
            {'error': f'Only {item.product.stock_qty} items available'},
            status=status.HTTP_400_BAD_REQUEST
        )

    item.quantity = quantity
    item.save()
    return Response(CartSerializer(cart).data)


@api_view(['DELETE'])
def remove_cart_item(request, item_id):
    cart = get_or_create_cart(request)
    try:
        CartItem.objects.get(id=item_id, cart=cart).delete()
    except CartItem.DoesNotExist:
        return Response({'error': 'Item not found'}, status=status.HTTP_404_NOT_FOUND)

    return Response(CartSerializer(cart).data)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def clear_cart(request):
    cart = get_or_create_cart(request)
    cart.items.all().delete()
    return Response({'message': 'Cart cleared'})