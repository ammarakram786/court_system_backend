from rest_framework.permissions import BasePermission
from django.utils import timezone
from django.db.models import Q
from .models import PermissionOverride

class HasPermissionCode(BasePermission):
    """
    Checks if user's role has the required permission code or if an ALLOW/DENY override applies.
    Supports:
      1) `required_permission = 'cases.manage'`
      2) `action_permissions = {'list': 'cases.view', 'create': 'cases.create'}`
    Superusers and staff always bypass.
    If no permission is required for the view/action, allows authenticated access.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_superuser or request.user.is_staff:
            return True

        # Check action-specific permission first, then view-level fallback
        action_permissions = getattr(view, 'action_permissions', {})
        action_name = getattr(view, 'action', None)
        required_permission = action_permissions.get(action_name) or getattr(view, 'required_permission', None)

        if not required_permission:
            return True

        # Check permission overrides (DENY takes precedence over ALLOW)
        now = timezone.now()
        active_overrides = PermissionOverride.objects.filter(
            user=request.user,
            permission_code=required_permission
        ).filter(
            Q(expires_at__isnull=True) | Q(expires_at__gt=now)
        )

        for override in active_overrides:
            if override.effect == PermissionOverride.Effect.DENY:
                return False
            if override.effect == PermissionOverride.Effect.ALLOW:
                return True

        # Check user's assigned role permissions
        if request.user.role_id:
            return request.user.role.permissions.filter(code=required_permission).exists()

        return False
