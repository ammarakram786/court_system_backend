import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils.translation import gettext_lazy as _

from core.models import TimeStampedModel
from .role import Role
from .organization import Rank, Appointment, Organization


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
        if not extra_fields.get('is_staff'):
            raise ValueError('Superuser must have is_staff=True.')
        if not extra_fields.get('is_superuser'):
            raise ValueError('Superuser must have is_superuser=True.')
        return self.create_user(username, svc_number, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin, TimeStampedModel):
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

    objects = UserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['svc_number', 'name']

    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    @property
    def id(self):
        return self.user_id

    def __str__(self):
        rank_abbr = f"{self.rank.abbreviation} " if self.rank and self.rank.abbreviation else ""
        return f"{rank_abbr}{self.name} ({self.svc_number})"
