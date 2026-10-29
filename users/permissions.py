from rest_framework.permissions import BasePermission
from django.utils import timezone
from .models import PermissionOverride

class HasPermissionCode(BasePermission):
    """
    Checks if user's role has the required permission code or if an ALLOW/DENY override applies.
    Usage: set `required_permission = 'cases.create_case'` on ViewSet.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_superuser or request.user.is_staff:
            return True

        required_permission = getattr(view, 'required_permission', None)
        if not required_permission:
            return True

        # Check permission overrides
        now = timezone.now()
        override = PermissionOverride.objects.filter(
            user=request.user,
            permission_code=required_permission
        ).filter(models_expires_filter(now)).first() if hasattr(PermissionOverride, 'objects') else None

        # Simplified override check without complex Q if needed
        overrides = PermissionOverride.objects.filter(user=request.user, permission_code=required_permission)
        for ov in overrides:
            if ov.expires_at and ov.expires_at < now:
                continue
            if ov.effect == PermissionOverride.Effect.DENY:
                return False
            if ov.effect == PermissionOverride.Effect.ALLOW:
                return True

        # Check role permissions
        if request.user.role:
            return request.user.role.permissions.filter(code=required_permission).exists()

        return False

def models_expires_filter(now):
    from django.db.models import Q
    return Q(expires_at__isnull=True) | Q(expires_at__gt=now)
