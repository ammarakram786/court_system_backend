# RBAC & Route Permission System (Skill Guide)

This guide documents the Role-Based Access Control (RBAC) architecture, the permission definition formula, route-level enforcement, and operational commands for the Django REST Framework backend.

---

## 1. Architecture Overview

The system uses a declarative, modular RBAC architecture designed for scalable Django REST Framework applications:

1. **Declarative Definitions**: Each Django application declares its capability permissions in `<app>/permission.py` using a standardized formula.
2. **App-Scoped Database Persistence**: The `Permission` model stores capability permissions keyed by unique `code_name`, grouped by `app_name` and `module_name`.
3. **Automated Synchronization**: A management command (`sync_permissions`) scans all installed apps and upserts permissions into the database idempotently.
4. **Route-Level Enforcement**: A DRF permission class (`HasPermissionCode`) inspects `action_permissions` on ViewSets and verifies against the user's role or explicit overrides.
5. **User Overrides**: Granular `ALLOW` and `DENY` overrides on a per-user, per-permission basis with optional expiration dates.

---

## 2. Permission Model Schema

Located in `accounts/models/permission.py`:

```python
class Permission(TimeStampedModel):
    permission_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    app_name = models.CharField(max_length=100, db_index=True, default='accounts')
    module_name = models.CharField(max_length=100, db_index=True)
    name = models.CharField(max_length=150)
    code_name = models.CharField(max_length=100, unique=True, db_index=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

### Key Fields:
- `app_name`: Django app identifier (e.g., `'accounts'`, `'courts'`).
- `module_name`: Domain model or functional group (e.g., `'Role'`, `'User'`, `'Organization'`, `'Case'`).
- `name`: Human-readable display label (e.g., `'Create Role'`, `'Read Cases'`).
- `code_name`: Unique system permission identifier (e.g., `'role_create'`, `'case_read'`).
- `description`: Detailed explanation of the capability granted.

---

## 3. The App Permission Formula (`<app>/permission.py`)

Every app exposes its permissions in `<app>/permission.py` using instantiations of `Permission`:

```python
from accounts.models import Permission

PERMISSIONS = [
    Permission(
        name='Show Role',
        code_name='show_create',
        module_name='Role',
        app_name='accounts',
        description='User can show role'
    ),
    Permission(
        name='Create Role',
        code_name='role_create',
        module_name='Role',
        app_name='accounts',
        description='User can create role'
    ),
    Permission(
        name='Read Role',
        code_name='role_read',
        module_name='Role',
        app_name='accounts',
        description='User can read role'
    ),
    Permission(
        name='Update Role',
        code_name='role_update',
        module_name='Role',
        app_name='accounts',
        description='User can update role'
    ),
    Permission(
        name='Delete Role',
        code_name='role_delete',
        module_name='Role',
        app_name='accounts',
        description='User can delete role'
    ),
]
```

### Standard Action Naming Convention:
- Read / View: `<module>_read`
- Create / Insert: `<module>_create`
- Update / Patch: `<module>_update`
- Delete / Destroy: `<module>_delete`
- Domain-specific actions: `<module>_<action>` (e.g., `case_close`)

---

## 4. Automated Permission Synchronization

### Command Line:
```bash
python manage.py sync_permissions
```

### Programmatic / Service:
```python
from accounts.services import permissions_sync

count = permissions_sync()
```

### How It Works:
1. Iterates over all installed apps via `django.apps.apps.get_app_configs()`.
2. Attempts to import `<app_name>.permission`.
3. Looks for `PERMISSIONS` or `<APP_NAME>_PERMISSIONS`.
4. Performs `Permission.objects.update_or_create(code_name=..., defaults={...})`.
5. Guarantees zero duplicate records and updates descriptions/names without breaking relational FKs.

---

## 5. Route-Level Permission Enforcement

### Permission Class: `HasPermissionCode`
Located in `accounts/permissions.py`:

```python
from rest_framework.permissions import IsAuthenticated
from accounts.permissions import HasPermissionCode

class RoleViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, HasPermissionCode]
    permission_prefix = 'role'
    action_permissions = {
        'list': 'role_read',
        'retrieve': 'role_read',
        'create': 'role_create',
        'update': 'role_update',
        'partial_update': 'role_update',
        'destroy': 'role_delete',
    }
```

### Action Mapping Rules:
1. **Explicit Action Mapping**: Matches `view.action` against keys in `action_permissions`.
2. **Unrestricted Actions**: If mapped to `None`, any authenticated user may access the endpoint:
   ```python
   action_permissions = {
       ...
       'me': None,               # Any authenticated user can view own profile
       'change_password': None,  # Any authenticated user can change own password
   }
   ```
3. **Prefix Fallback**: If `view.action` is not in `action_permissions`, but `permission_prefix` is set on the ViewSet:
   - `list` / `retrieve` -> `<permission_prefix>_read`
   - `create` -> `<permission_prefix>_create`
   - `update` / `partial_update` -> `<permission_prefix>_update`
   - `destroy` -> `<permission_prefix>_delete`

---

## 6. Permission Resolution Flowchart

When a request reaches a protected route:

```
                  [ Incoming Request ]
                            │
               Is user authenticated?
                     ├── No  ──> [ HTTP 401 Unauthorized ]
                     └── Yes
                            │
            Is user superuser or staff?
                     ├── Yes ──> [ Allow Access (200/201) ]
                     └── No
                            │
         Identify required permission code
           (from action_permissions / prefix)
                            │
            Is required permission None?
                     ├── Yes ──> [ Allow Access ]
                     └── No
                            │
            Check active PermissionOverrides
              (user=request.user, code=required)
                            │
                     ┌──────┴──────┐
                  DENY           ALLOW
                     │             │
             [ 403 Forbidden ]  [ Allow Access ]
                     │
              No Override Match
                     │
           Check assigned Role permissions
          (request.user.role.permissions)
                     ├── Matched ──> [ Allow Access ]
                     └── No Role / No Match ──> [ 403 Forbidden ]
```

---

## 7. User Permission Overrides

When an exceptional grant or temporary restriction is needed for a specific user:

```python
from accounts.models import PermissionOverride

# Temporarily revoke case creation from a user
PermissionOverride.objects.create(
    user=user,
    permission_code='case_create',
    effect=PermissionOverride.Effect.DENY,
    reason='Audit pending on previous submissions',
    granted_by='admin_officer',
    expires_at=timezone.now() + timedelta(days=7)
)

# Grant one-off access without modifying their role
PermissionOverride.objects.create(
    user=user,
    permission_code='organization_create',
    effect=PermissionOverride.Effect.ALLOW,
    reason='Special administrative restructuring task',
    granted_by='hq_commander'
)
```

---

## 8. Accounts & Organizations Unified Architecture

Organizations, Ranks, and Appointments are merged directly into `accounts`:

```
accounts/
├── models/
│   ├── permission.py       # Permission model with app_name & code_name
│   ├── role.py             # Role & RolePermission (M2M)
│   ├── override.py         # PermissionOverride (ALLOW / DENY)
│   ├── organization.py     # Organization, Rank, Appointment
│   └── user.py             # User model with Rank, Appt, Org, Role FKs
├── serializers/
│   ├── permission.py
│   ├── role.py
│   ├── user.py
│   ├── organization.py     # OrganizationSerializer, RankSerializer, AppointmentSerializer
│   └── override.py
├── selectors.py            # Optimized querysets with select_related / prefetch_related
├── services.py             # Domain mutations & permissions_sync()
├── permissions.py          # HasPermissionCode DRF validator
├── permission.py           # USER_PERMISSIONS declarative formula definitions
├── views/
│   ├── permission.py
│   ├── role.py
│   ├── user.py
│   ├── organization.py     # OrganizationViewSet, RankViewSet, AppointmentViewSet
│   └── override.py
└── urls.py                 # Unified router for all accounts and organization endpoints
```

---

## 9. Developer Step-by-Step: Adding a New Module

1. **Create the Model**:
   Define your model in `<app>/models/<domain>.py`.
2. **Declare Permissions in `<app>/permission.py`**:
   ```python
   from accounts.models import Permission

   PERMISSIONS += [
       Permission(name='Create Document', code_name='document_create', module_name='Document', app_name='cases', description='User can upload document'),
       Permission(name='Read Document', code_name='document_read', module_name='Document', app_name='cases', description='User can read document'),
       Permission(name='Delete Document', code_name='document_delete', module_name='Document', app_name='cases', description='User can delete document'),
   ]
   ```
3. **Synchronize Database**:
   ```bash
   python manage.py sync_permissions
   ```
4. **Protect the ViewSet**:
   ```python
   from accounts.permissions import HasPermissionCode

   class DocumentViewSet(viewsets.ModelViewSet):
       permission_classes = [IsAuthenticated, HasPermissionCode]
       permission_prefix = 'document'
       action_permissions = {
           'list': 'document_read',
           'retrieve': 'document_read',
           'create': 'document_create',
           'destroy': 'document_delete',
       }
   ```
5. **Verify with Tests**:
   Create a test user with a role possessing the permission (verify 200/201), a test user without the permission (verify 403), and test an override.
