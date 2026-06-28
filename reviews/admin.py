from django.contrib import admin
from .models import Review

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['user', 'product', 'rating', 'status', 'is_flagged', 'moderated_by', 'created_at']
    list_filter = ['status', 'is_flagged', 'rating', 'created_at']
    search_fields = ['user__username', 'product__name', 'comment']
    list_editable = ['status']
    readonly_fields = ['moderated_by', 'moderated_at', 'created_at', 'updated_at']

    actions = ['approve_reviews', 'reject_reviews']

    def approve_reviews(self, request, queryset):
        queryset.update(status='approved', is_approved=True, moderated_by=request.user)
        self.message_user(request, f"{queryset.count()} reviews approved.")

    def reject_reviews(self, request, queryset):
        queryset.update(status='rejected', is_approved=False, moderated_by=request.user)
        self.message_user(request, f"{queryset.count()} reviews rejected.")

    approve_reviews.short_description = "✅ Approve selected reviews"
    reject_reviews.short_description = "❌ Reject selected reviews"