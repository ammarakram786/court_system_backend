from django.db.models import QuerySet, Count
from .models import User, Role, Permission, PermissionOverride, Organization, Rank, Appointment


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


def role_get(*, role_id) -> Role:
    return Role.objects.prefetch_related('permissions').get(pk=role_id)


def permission_list() -> QuerySet[Permission]:
    return Permission.objects.all()


def permission_override_list() -> QuerySet[PermissionOverride]:
    return PermissionOverride.objects.select_related('user').all()


def organization_list() -> QuerySet[Organization]:
    return Organization.objects.select_related('parent_organization').annotate(
        _sub_organizations_count=Count('sub_organizations')
    ).all()


def organization_get(*, organization_id) -> Organization:
    return Organization.objects.select_related('parent_organization').annotate(
        _sub_organizations_count=Count('sub_organizations')
    ).get(pk=organization_id)


def rank_list() -> QuerySet[Rank]:
    return Rank.objects.all()


def appointment_list() -> QuerySet[Appointment]:
    return Appointment.objects.all()
