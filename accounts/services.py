import importlib
from django.apps import apps
from django.core.exceptions import ValidationError
from .models import User, Role, Permission, PermissionOverride, Organization, Rank, Appointment


def user_create(*, username, name, svc_number, organization=None, role=None, password=None, **kwargs) -> User:
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


def role_update(*, role: Role, **kwargs) -> Role:
    permission_ids = kwargs.pop('permission_ids', None)
    for field, value in kwargs.items():
        setattr(role, field, value)
    role.full_clean()
    role.save()
    if permission_ids is not None:
        permissions = Permission.objects.filter(pk__in=permission_ids)
        role.permissions.set(permissions)
    return role


def organization_create(*, parent_organization=None, name: str, code: str, is_active: bool = True) -> Organization:
    org = Organization(
        parent_organization=parent_organization,
        name=name,
        code=code,
        is_active=is_active
    )
    org.full_clean()
    org.save()
    return org


def organization_update(*, organization: Organization, **kwargs) -> Organization:
    for field, value in kwargs.items():
        setattr(organization, field, value)
    organization.full_clean()
    organization.save()
    return organization


def rank_create(*, title: str, abbreviation: str = None, seniority_index: int = 0) -> Rank:
    rank = Rank.objects.create(
        title=title,
        abbreviation=abbreviation,
        seniority_index=seniority_index
    )
    return rank


def appointment_create(*, title: str, appointment_code: str = None) -> Appointment:
    appointment = Appointment.objects.create(
        title=title,
        appointment_code=appointment_code
    )
    return appointment


def permission_override_create(*, user: User, permission_code: str, effect: str, reason: str, granted_by: str, expires_at=None) -> PermissionOverride:
    override = PermissionOverride.objects.create(
        user=user,
        permission_code=permission_code,
        effect=effect,
        reason=reason,
        granted_by=granted_by,
        expires_at=expires_at
    )
    return override


def permissions_sync() -> int:
    synced_count = 0
    for app_config in apps.get_app_configs():
        try:
            mod = importlib.import_module(f"{app_config.name}.permission")
            perms = getattr(mod, 'PERMISSIONS', None) or getattr(mod, f"{app_config.name.upper()}_PERMISSIONS", None)
            if perms:
                for p in perms:
                    app_name = getattr(p, 'app_name', None) or app_config.name
                    Permission.objects.update_or_create(
                        code_name=p.code_name,
                        defaults={
                            'name': p.name,
                            'module_name': p.module_name,
                            'app_name': app_name,
                            'description': p.description,
                        }
                    )
                    synced_count += 1
        except ModuleNotFoundError:
            continue
    return synced_count
