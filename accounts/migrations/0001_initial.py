import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='Appointment',
            fields=[
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('appointment_id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('title', models.CharField(max_length=150, unique=True)),
                ('appointment_code', models.CharField(blank=True, max_length=50, null=True, unique=True)),
            ],
            options={
                'verbose_name': 'Appointment',
                'verbose_name_plural': 'Appointments',
                'db_table': 'appointments',
            },
        ),
        migrations.CreateModel(
            name='Rank',
            fields=[
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('rank_id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('title', models.CharField(max_length=100, unique=True)),
                ('abbreviation', models.CharField(blank=True, max_length=20, null=True)),
                ('seniority_index', models.IntegerField(db_index=True, default=0)),
            ],
            options={
                'verbose_name': 'Rank',
                'verbose_name_plural': 'Ranks',
                'db_table': 'ranks',
                'ordering': ['seniority_index'],
            },
        ),
        migrations.CreateModel(
            name='Organization',
            fields=[
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('organization_id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=150, unique=True)),
                ('code', models.CharField(db_index=True, max_length=50, unique=True)),
                ('org_level', models.PositiveIntegerField(default=1)),
                ('is_active', models.BooleanField(default=True)),
                ('is_root', models.BooleanField(db_index=True, default=False, editable=False)),
                ('parent_organization', models.ForeignKey(blank=True, db_column='parent_organization_id', null=True, on_delete=django.db.models.deletion.PROTECT, related_name='sub_organizations', to='accounts.organization')),
            ],
            options={
                'verbose_name': 'Organization',
                'verbose_name_plural': 'Organizations',
                'db_table': 'organizations',
                'ordering': ['org_level', 'name'],
                'constraints': [models.UniqueConstraint(condition=models.Q(('is_root', True)), fields=('is_root',), name='unique_single_root_organization')],
            },
        ),
        migrations.CreateModel(
            name='Permission',
            fields=[
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('permission_id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('app_name', models.CharField(db_index=True, default='accounts', max_length=100)),
                ('module_name', models.CharField(db_index=True, max_length=100)),
                ('name', models.CharField(max_length=150)),
                ('code_name', models.CharField(db_index=True, max_length=100, unique=True)),
                ('description', models.TextField(blank=True, null=True)),
            ],
            options={
                'verbose_name': 'Permission',
                'verbose_name_plural': 'Permissions',
                'db_table': 'permissions',
                'ordering': ['app_name', 'module_name', 'name'],
            },
        ),
        migrations.CreateModel(
            name='Role',
            fields=[
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('role_id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=100, unique=True)),
                ('description', models.TextField(blank=True, null=True)),
            ],
            options={
                'verbose_name': 'Role',
                'verbose_name_plural': 'Roles',
                'db_table': 'roles',
            },
        ),
        migrations.CreateModel(
            name='RolePermission',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('permission', models.ForeignKey(db_column='permission_id', on_delete=django.db.models.deletion.CASCADE, to='accounts.permission')),
                ('role', models.ForeignKey(db_column='role_id', on_delete=django.db.models.deletion.CASCADE, to='accounts.role')),
            ],
            options={
                'db_table': 'role_permissions',
                'constraints': [models.UniqueConstraint(fields=('role', 'permission'), name='unique_role_permission')],
            },
        ),
        migrations.AddField(
            model_name='role',
            name='permissions',
            field=models.ManyToManyField(related_name='roles', through='accounts.RolePermission', to='accounts.permission'),
        ),
        migrations.CreateModel(
            name='User',
            fields=[
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user_id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('username', models.CharField(db_index=True, max_length=100, unique=True)),
                ('name', models.CharField(max_length=200)),
                ('profile_status', models.CharField(choices=[('ACTIVE', 'Active'), ('INACTIVE', 'Inactive'), ('SUSPENDED', 'Suspended'), ('ON_LEAVE', 'On Leave'), ('ARCHIVED', 'Archived')], default='ACTIVE', max_length=30)),
                ('svc_number', models.CharField(db_index=True, max_length=100, unique=True)),
                ('profile_image', models.CharField(blank=True, max_length=500, null=True)),
                ('is_staff', models.BooleanField(default=False)),
                ('is_active', models.BooleanField(default=True)),
                ('appointment', models.ForeignKey(blank=True, db_column='appointment_id', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='users', to='accounts.appointment')),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.group', verbose_name='groups')),
                ('organization', models.ForeignKey(blank=True, db_column='organization_id', null=True, on_delete=django.db.models.deletion.PROTECT, related_name='users', to='accounts.organization')),
                ('rank', models.ForeignKey(blank=True, db_column='rank_id', null=True, on_delete=django.db.models.deletion.PROTECT, related_name='users', to='accounts.rank')),
                ('role', models.ForeignKey(blank=True, db_column='role_id', null=True, on_delete=django.db.models.deletion.PROTECT, related_name='users', to='accounts.role')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.permission', verbose_name='user permissions')),
            ],
            options={
                'verbose_name': 'User',
                'verbose_name_plural': 'Users',
                'db_table': 'users',
            },
        ),
        migrations.CreateModel(
            name='PermissionOverride',
            fields=[
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('override_id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('permission_code', models.CharField(db_index=True, max_length=100)),
                ('effect', models.CharField(choices=[('ALLOW', 'Allow'), ('DENY', 'Deny')], max_length=10)),
                ('reason', models.TextField()),
                ('granted_by', models.CharField(max_length=200)),
                ('expires_at', models.DateTimeField(blank=True, null=True)),
                ('user', models.ForeignKey(db_column='user_id', on_delete=django.db.models.deletion.CASCADE, related_name='permission_overrides', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Permission Override',
                'verbose_name_plural': 'Permission Overrides',
                'db_table': 'permission_overrides',
                'constraints': [models.UniqueConstraint(fields=('user', 'permission_code'), name='unique_user_permission_override')],
            },
        ),
    ]
