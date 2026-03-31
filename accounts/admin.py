from django.contrib import admin
from .models import User, SecurityAuditLog

admin.site.register(User)

@admin.register(SecurityAuditLog)
class SecurityAuditLogAdmin(admin.ModelAdmin):
    list_display = ('action_type', 'user', 'ip_address', 'timestamp')
    list_filter = ('action_type', 'timestamp')
    search_fields = ('user__email', 'ip_address', 'details')
    readonly_fields = ('action_type', 'user', 'ip_address', 'details', 'timestamp')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
