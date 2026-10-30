import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils.translation import gettext_lazy as _
from organizations.models import Rank, Appointment, Organization

class Permission(models.Model):
    permission_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=100, unique=True, db_index=True)
    module = models.CharField(max_length=100, db_index=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'permissions'
        verbose_name = 'Permission'
        verbose_name_plural = 'Permissions'

    def __str__(self):
        return f"[{self.module}] {self.code}"


class Role(models.Model):
    role_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    permissions = models.ManyToManyField(
        Permission,
        through='RolePermission',
        related_name='roles'
    )

    class Meta:
        db_table = 'roles'
        verbose_name = 'Role'
        verbose_name_plural = 'Roles'

    def __str__(self):
        return self.name


class RolePermission(models.Model):
    role = models.ForeignKey(Role, on_delete=models.CASCADE, db_column='role_id')
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE, db_column='permission_id')

    class Meta:
        db_table = 'role_permissions'
        constraints = [
            models.UniqueConstraint(fields=['role', 'permission'], name='unique_role_permission')
        ]


class UserManager(BaseUserManager):
    def create_user(self, username, svc_number, password=None, **extra_fields):
        if not username:
            raise ValueError('The Username field must be set')
        if not svc_number:
            raise ValueError('The Service Number field must be set')
        user = self.model(username=username, svc_number=svc_number, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, username, svc_number, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('profile_status', 'ACTIVE')
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        return self.create_user(username, svc_number, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    class ProfileStatus(models.TextChoices):
        ACTIVE = 'ACTIVE', _('Active')
        INACTIVE = 'INACTIVE', _('Inactive')
        SUSPENDED = 'SUSPENDED', _('Suspended')
        ON_LEAVE = 'ON_LEAVE', _('On Leave')
        ARCHIVED = 'ARCHIVED', _('Archived')

    user_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = models.CharField(max_length=100, unique=True, db_index=True)
    name = models.CharField(max_length=200)
    profile_status = models.CharField(
        max_length=30,
        choices=ProfileStatus.choices,
        default=ProfileStatus.ACTIVE
    )
    svc_number = models.CharField(max_length=100, unique=True, db_index=True)
    rank = models.ForeignKey(
        Rank,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='users',
        db_column='rank_id'
    )
    appointment = models.ForeignKey(
        Appointment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users',
        db_column='appointment_id'
    )
    organization = models.ForeignKey(
        Organization,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='users',
        db_column='organization_id'
    )
    role = models.ForeignKey(
        Role,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='users',
        db_column='role_id'
    )
    profile_image = models.CharField(max_length=500, blank=True, null=True)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['svc_number', 'name']

    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        rank_abbr = f"{self.rank.abbreviation} " if self.rank and self.rank.abbreviation else ""
        return f"{rank_abbr}{self.name} ({self.svc_number})"


class PermissionOverride(models.Model):
    class Effect(models.TextChoices):
        ALLOW = 'ALLOW', _('Allow')
        DENY = 'DENY', _('Deny')

    override_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='permission_overrides',
        db_column='user_id'
    )
    permission_code = models.CharField(max_length=100, db_index=True)
    effect = models.CharField(max_length=10, choices=Effect.choices)
    reason = models.TextField()
    granted_by = models.CharField(max_length=200)
    expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'permission_overrides'
        constraints = [
            models.UniqueConstraint(fields=['user', 'permission_code'], name='unique_user_permission_override')
        ]
