from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import serializers
from .models import AuditLog

class AuditLogSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()

    class Meta:
        model = AuditLog
        fields = '__all__'

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def audit_logs(request):
    if not request.user.is_staff:
        return Response({'error': 'Admin only'}, status=403)

    logs = AuditLog.objects.all()[:100]  # آخر 100 عملية
    serializer = AuditLogSerializer(logs, many=True)
    return Response(serializer.data)