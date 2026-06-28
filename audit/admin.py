from django.contrib import admin
from .models import AuditLog

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'action', 'model_name', 'object_repr', 'ip_address', 'timestamp']
    list_filter = ['action', 'model_name', 'timestamp']
    search_fields = ['user__username', 'object_repr', 'ip_address']
    readonly_fields = ['user', 'action', 'model_name', 'object_id',
                      'object_repr', 'ip_address', 'timestamp', 'extra_data']

    def has_add_permission(self, request):
        return False   # ما أحد يضيف log يدوياً

    def has_delete_permission(self, request, obj=None):
        return False   # ما أحد يحذف الـ logs