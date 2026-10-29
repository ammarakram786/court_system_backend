from django.core.exceptions import ValidationError
from .models import User, Role, Permission, PermissionOverride

def user_create(*, username, name, svc_number, organization, role, password=None, **kwargs) -> User:
    user = User.objects.create_user(
        username=username,
        name=name,
        svc_number=svc_number,
        organization=organization,
        role=role,
        password=password,
        **kwargs
    )
    return user

def user_update(*, user: User, **kwargs) -> User:
    password = kwargs.pop('password', None)
    for field, value in kwargs.items():
        setattr(user, field, value)
    if password:
        user.set_password(password)
    user.full_clean()
    user.save()
    return user

def role_create(*, name: str, description: str = None, permission_ids: list = None) -> Role:
    role = Role.objects.create(name=name, description=description)
    if permission_ids:
        permissions = Permission.objects.filter(pk__in=permission_ids)
        role.permissions.set(permissions)
    return role

def permission_override_create(*, user: User, permission_code: str, effect: str, reason: str, granted_by: str, expires_at=None) -> PermissionOverride:
    override, _ = PermissionOverride.objects.update_or_create(
        user=user,
        permission_code=permission_code,
        defaults={
            'effect': effect,
            'reason': reason,
            'granted_by': granted_by,
            'expires_at': expires_at
        }
    )
    return override
