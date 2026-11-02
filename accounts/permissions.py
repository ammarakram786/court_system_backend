from rest_framework.permissions import BasePermission
from django.utils import timezone
from django.db.models import Q

from accounts.models import PermissionOverride
from .permission import USER_PERMISSIONS, ACCOUNT_PERMISSIONS, PERMISSIONS


class HasPermissionCode(BasePermission):
    """
    Checks if user's role has the required permission code or if an ALLOW/DENY override applies.
    Supports:
      1) `required_permission = 'role_read'`
      2) `action_permissions = {'list': 'role_read', 'create': 'role_create', ...}`
      3) `permission_prefix = 'role'` with automatic action fallback:
         - list/retrieve -> <prefix>_read
         - create -> <prefix>_create
         - update/partial_update -> <prefix>_update
         - destroy -> <prefix>_delete

    Staff and superusers automatically bypass.
    If no permission requirement is specified, authenticated users are permitted.
    """
    ACTION_SUFFIX_MAP = {
        'list': '_read',
        'retrieve': '_read',
        'create': '_create',
        'update': '_update',
        'partial_update': '_update',
        'destroy': '_delete',
    }

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_superuser or request.user.is_staff:
            return True

        action_permissions = getattr(view, 'action_permissions', {})
        action_name = getattr(view, 'action', None)

        required_permission = None
        if action_name in action_permissions:
            required_permission = action_permissions[action_name]
            if required_permission is None:
                return True
        else:
            required_permission = getattr(view, 'required_permission', None)

        if not required_permission and hasattr(view, 'permission_prefix') and action_name:
            suffix = self.ACTION_SUFFIX_MAP.get(action_name)
            if suffix:
                required_permission = f"{view.permission_prefix}{suffix}"

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
        if getattr(request.user, 'role_id', None):
            return request.user.role.permissions.filter(
                Q(code_name=required_permission)
            ).exists()

        return False
