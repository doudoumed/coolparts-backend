from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Cart, CartItem
from .serializers import CartSerializer
from products.models import Product

def get_or_create_cart(request):
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)
    else:
        if not request.session.session_key:
            request.session.create()
        cart, _ = Cart.objects.get_or_create(session_key=request.session.session_key)
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

    product = Product.objects.get(id=product_id)
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
    item = CartItem.objects.get(id=item_id, cart=cart)
    item.quantity = int(request.data.get('quantity', item.quantity))
    item.save()
    return Response(CartSerializer(cart).data)

@api_view(['DELETE'])
def remove_cart_item(request, item_id):
    cart = get_or_create_cart(request)
    CartItem.objects.filter(id=item_id, cart=cart).delete()
    return Response(CartSerializer(cart).data)