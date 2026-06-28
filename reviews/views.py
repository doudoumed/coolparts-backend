from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Review
from .serializers import ReviewSerializer, AdminReviewSerializer
from .utils import check_for_banned_words
from products.models import Product
from audit.utils import log_action


# ─── Customer Views ────────────────────────────────────────────

@api_view(['GET'])
def product_reviews(request, product_id):
    """عرض التقييمات الموافق عليها فقط"""
    try:
        product = Product.objects.get(id=product_id, is_active=True)
    except Product.DoesNotExist:
        return Response({'error': 'Product not found'}, status=404)

    reviews = Review.objects.filter(
        product=product, status='approved'
    ).select_related('user')

    ordering = request.query_params.get('ordering', '-created_at')
    if ordering in ['created_at', '-created_at', 'rating', '-rating']:
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
    """إضافة تقييم جديد — يروح pending انتظار موافقة الأدمن"""
    try:
        product = Product.objects.get(id=product_id, is_active=True)
    except Product.DoesNotExist:
        return Response({'error': 'Product not found'}, status=404)

    if Review.objects.filter(product=product, user=request.user).exists():
        return Response(
            {'error': 'You have already reviewed this product'},
            status=status.HTTP_400_BAD_REQUEST
        )

    serializer = ReviewSerializer(data=request.data)
    if serializer.is_valid():
        comment = serializer.validated_data.get('comment', '')
        is_flagged, flag_reason = check_for_banned_words(comment)

        review = serializer.save(
            product=product,
            user=request.user,
            status='pending',
            is_approved=False,
            is_flagged=is_flagged,
            flag_reason=flag_reason
        )

        log_action(request, 'CREATE', 'Review',
                   object_id=review.id,
                   object_repr=f"{request.user.username} - {product.name}")

        return Response({
            'message': 'Review submitted and pending approval',
            'review': serializer.data
        }, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_review(request, product_id, review_id):
    """تعديل تقييم — يرجع لـ pending بعد التعديل"""
    try:
        review = Review.objects.get(
            id=review_id, product_id=product_id, user=request.user
        )
    except Review.DoesNotExist:
        return Response({'error': 'Review not found'}, status=404)

    serializer = ReviewSerializer(
        review, data=request.data,
        partial=(request.method == 'PATCH')
    )
    if serializer.is_valid():
        comment = serializer.validated_data.get('comment', review.comment)
        is_flagged, flag_reason = check_for_banned_words(comment)

        serializer.save(
            status='pending',
            is_approved=False,
            is_flagged=is_flagged,
            flag_reason=flag_reason
        )

        log_action(request, 'UPDATE', 'Review',
                   object_id=review.id,
                   object_repr=f"{request.user.username} - {review.product.name}")

        return Response({
            'message': 'Review updated and pending approval',
            'review': serializer.data
        })

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
        return Response({'error': 'Review not found'}, status=404)

    log_action(request, 'DELETE', 'Review',
               object_id=review.id,
               object_repr=f"{request.user.username} - {review.product.name}")
    review.delete()
    return Response({'message': 'Review deleted'}, status=204)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_reviews(request):
    """تقييمات المستخدم الحالي"""
    reviews = Review.objects.filter(
        user=request.user
    ).select_related('product')
    serializer = ReviewSerializer(reviews, many=True)
    return Response(serializer.data)


# ─── Admin Views ───────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_list_reviews(request):
    """الأدمن يشوف كل التقييمات مع فلترة"""
    if not request.user.is_staff:
        return Response({'error': 'Admin only'}, status=403)

    reviews = Review.objects.all().select_related('user', 'product', 'moderated_by')

    # فلترة بالحالة
    status_filter = request.query_params.get('status')
    if status_filter in ['pending', 'approved', 'rejected']:
        reviews = reviews.filter(status=status_filter)

    # فلترة بالتقييمات المبلّغ عنها
    flagged = request.query_params.get('flagged')
    if flagged == 'true':
        reviews = reviews.filter(is_flagged=True)

    # فلترة بالمنتج
    product_id = request.query_params.get('product')
    if product_id:
        reviews = reviews.filter(product_id=product_id)

    serializer = AdminReviewSerializer(reviews, many=True)
    return Response({
        'total': reviews.count(),
        'reviews': serializer.data
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def moderate_review(request, review_id):
    """الأدمن يوافق أو يرفض تقييم"""
    if not request.user.is_staff:
        return Response({'error': 'Admin only'}, status=403)

    try:
        review = Review.objects.get(id=review_id)
    except Review.DoesNotExist:
        return Response({'error': 'Review not found'}, status=404)

    action_taken = request.data.get('action')  # 'approve' أو 'reject'

    if action_taken not in ['approve', 'reject']:
        return Response(
            {'error': 'Action must be approve or reject'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if action_taken == 'approve':
        review.status = 'approved'
        review.is_approved = True
    else:
        review.status = 'rejected'
        review.is_approved = False

    review.moderated_by = request.user
    review.moderated_at = timezone.now()
    review.save()

    log_action(request, 'UPDATE', 'Review',
               object_id=review.id,
               object_repr=f"{'Approved' if action_taken == 'approve' else 'Rejected'}: {review.user.username} - {review.product.name}")

    return Response({
        'message': f'Review {action_taken}d successfully',
        'review': AdminReviewSerializer(review).data
    })


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def admin_delete_review(request, review_id):
    """الأدمن يحذف أي تقييم"""
    if not request.user.is_staff:
        return Response({'error': 'Admin only'}, status=403)

    try:
        review = Review.objects.get(id=review_id)
    except Review.DoesNotExist:
        return Response({'error': 'Review not found'}, status=404)

    log_action(request, 'DELETE', 'Review',
               object_id=review.id,
               object_repr=f"Admin deleted: {review.user.username} - {review.product.name}")
    review.delete()
    return Response({'message': 'Review deleted by admin'}, status=204)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_review_stats(request):
    """إحصائيات التقييمات للأدمن"""
    if not request.user.is_staff:
        return Response({'error': 'Admin only'}, status=403)

    return Response({
        'total': Review.objects.count(),
        'pending': Review.objects.filter(status='pending').count(),
        'approved': Review.objects.filter(status='approved').count(),
        'rejected': Review.objects.filter(status='rejected').count(),
        'flagged': Review.objects.filter(is_flagged=True).count(),
    })