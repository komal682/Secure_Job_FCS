from django.contrib.auth.signals import user_logged_in, user_login_failed
from django.dispatch import receiver
from .models import SecurityAuditLog
import logging

logger = logging.getLogger(__name__)

def get_client_ip(request):
    if not request:
        return None
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    ip = get_client_ip(request)
    SecurityAuditLog.objects.create(
        action_type='LOGIN_SUCCESS',
        user=user,
        ip_address=ip,
        details=f'User {user.email} successfully logged in.'
    )

@receiver(user_login_failed)
def log_user_login_failed(sender, credentials, request, **kwargs):
    ip = get_client_ip(request)
    email = credentials.get('email', 'Unknown')
    SecurityAuditLog.objects.create(
        action_type='LOGIN_FAILED',
        user=None,
        ip_address=ip,
        details=f'Failed login attempt for email: {email}'
    )
