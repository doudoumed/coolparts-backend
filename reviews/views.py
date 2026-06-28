from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from .models import Review
from .serializers import ReviewSerializer
from products.models import Product
from audit.utils import log_action

@api_view(['GET'])
def product_reviews(request, product_id):
    """عرض كل تقييمات منتج معين"""
    try:
        product = Product.objects.get(id=product_id, is_active=True)
    except Product.DoesNotExist:
        return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)

    reviews = Review.objects.filter(
        product=product, is_approved=True
    ).select_related('user')

    # ترتيب التقييمات
    ordering = request.query_params.get('ordering', '-created_at')
    valid_orderings = ['created_at', '-created_at', 'rating', '-rating']
    if ordering in valid_orderings:
        reviews = reviews.order_by(ordering)

    serializer = ReviewSerializer(reviews, many=True)
    return Response({
        'product': product.name,
        'average_rating': product.average_rating(),
        'review_count': product.review_count(),
        'reviews': serializer.data
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_review(request, product_id):
    """إضافة تقييم جديد"""
    try:
        product = Product.objects.get(id=product_id, is_active=True)
    except Product.DoesNotExist:
        return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)

    # تحقق إذا المستخدم قيّم هذا المنتج قبل
    if Review.objects.filter(product=product, user=request.user).exists():
        return Response(
            {'error': 'You have already reviewed this product'},
            status=status.HTTP_400_BAD_REQUEST
        )

    serializer = ReviewSerializer(data=request.data)
    if serializer.is_valid():
        review = serializer.save(product=product, user=request.user)
        log_action(request, 'CREATE', 'Review',
                  object_id=review.id,
                  object_repr=f"{request.user.username} - {product.name}")
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_review(request, product_id, review_id):
    """تعديل تقييم موجود"""
    try:
        review = Review.objects.get(
            id=review_id, product_id=product_id, user=request.user
        )
    except Review.DoesNotExist:
        return Response({'error': 'Review not found'}, status=status.HTTP_404_NOT_FOUND)

    serializer = ReviewSerializer(
        review, data=request.data,
        partial=(request.method == 'PATCH')
    )
    if serializer.is_valid():
        serializer.save()
        log_action(request, 'UPDATE', 'Review',
                  object_id=review.id,
                  object_repr=f"{request.user.username} - {review.product.name}")
        return Response(serializer.data)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_review(request, product_id, review_id):
    """حذف تقييم"""
    try:
        review = Review.objects.get(
            id=review_id, product_id=product_id, user=request.user
        )
    except Review.DoesNotExist:
        return Response({'error': 'Review not found'}, status=status.HTTP_404_NOT_FOUND)

    log_action(request, 'DELETE', 'Review',
              object_id=review.id,
              object_repr=f"{request.user.username} - {review.product.name}")
    review.delete()
    return Response({'message': 'Review deleted'}, status=status.HTTP_204_NO_CONTENT)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_reviews(request):
    """عرض كل تقييمات المستخدم الحالي"""
    reviews = Review.objects.filter(
        user=request.user
    ).select_related('product')
    serializer = ReviewSerializer(reviews, many=True)
    return Response(serializer.data)