from django.db.models import QuerySet
from .models import User, Role, Permission, PermissionOverride

def user_list() -> QuerySet[User]:
    return User.objects.select_related(
        'rank', 'appointment', 'organization', 'role'
    ).prefetch_related('role__permissions').all()

def user_get(*, user_id) -> User:
    return User.objects.select_related(
        'rank', 'appointment', 'organization', 'role'
    ).prefetch_related('role__permissions').get(pk=user_id)

def role_list() -> QuerySet[Role]:
    return Role.objects.prefetch_related('permissions').all()

def permission_list() -> QuerySet[Permission]:
    return Permission.objects.all()
