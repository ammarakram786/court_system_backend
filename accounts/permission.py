from accounts.models import Permission

USER_PERMISSIONS = [
    # Role Permissions
    Permission(name='Show Role', code_name='show_create', module_name='Role', app_name='accounts', description='User can Show role'),
    Permission(name='Show Role Detail', code_name='role_show', module_name='Role', app_name='accounts', description='User can view role detail'),
    Permission(name='Create Role', code_name='role_create', module_name='Role', app_name='accounts', description='User can create role'),
    Permission(name='Read Role', code_name='role_read', module_name='Role', app_name='accounts', description='User can read role'),
    Permission(name='Update Role', code_name='role_update', module_name='Role', app_name='accounts', description='User can update role'),
    Permission(name='Delete Role', code_name='role_delete', module_name='Role', app_name='accounts', description='User can delete role'),

    # User Permissions
    Permission(name='Create User', code_name='user_create', module_name='User', app_name='accounts', description='User can create user'),
    Permission(name='Read User', code_name='user_read', module_name='User', app_name='accounts', description='User can read user'),
    Permission(name='Update User', code_name='user_update', module_name='User', app_name='accounts', description='User can update user'),
    Permission(name='Delete User', code_name='user_delete', module_name='User', app_name='accounts', description='User can delete user'),

    # Organization Permissions
    Permission(name='Create Organization', code_name='organization_create', module_name='Organization', app_name='accounts', description='User can create organization'),
    Permission(name='Read Organization', code_name='organization_read', module_name='Organization', app_name='accounts', description='User can read organization'),
    Permission(name='Update Organization', code_name='organization_update', module_name='Organization', app_name='accounts', description='User can update organization'),
    Permission(name='Delete Organization', code_name='organization_delete', module_name='Organization', app_name='accounts', description='User can delete organization'),

    # Rank Permissions
    Permission(name='Create Rank', code_name='rank_create', module_name='Rank', app_name='accounts', description='User can create rank'),
    Permission(name='Read Rank', code_name='rank_read', module_name='Rank', app_name='accounts', description='User can read rank'),
    Permission(name='Update Rank', code_name='rank_update', module_name='Rank', app_name='accounts', description='User can update rank'),
    Permission(name='Delete Rank', code_name='rank_delete', module_name='Rank', app_name='accounts', description='User can delete rank'),

    # Appointment Permissions
    Permission(name='Create Appointment', code_name='appointment_create', module_name='Appointment', app_name='accounts', description='User can create appointment'),
    Permission(name='Read Appointment', code_name='appointment_read', module_name='Appointment', app_name='accounts', description='User can read appointment'),
    Permission(name='Update Appointment', code_name='appointment_update', module_name='Appointment', app_name='accounts', description='User can update appointment'),
    Permission(name='Delete Appointment', code_name='appointment_delete', module_name='Appointment', app_name='accounts', description='User can delete appointment'),

    # Permission & Override Permissions
    Permission(name='Read Permission', code_name='permission_read', module_name='Permission', app_name='accounts', description='User can read permission list'),
    Permission(name='Create Override', code_name='override_create', module_name='PermissionOverride', app_name='accounts', description='User can create permission override'),
    Permission(name='Read Override', code_name='override_read', module_name='PermissionOverride', app_name='accounts', description='User can read permission override'),
    Permission(name='Update Override', code_name='override_update', module_name='PermissionOverride', app_name='accounts', description='User can update permission override'),
    Permission(name='Delete Override', code_name='override_delete', module_name='PermissionOverride', app_name='accounts', description='User can delete permission override'),
]

ACCOUNT_PERMISSIONS = USER_PERMISSIONS
PERMISSIONS = USER_PERMISSIONS
