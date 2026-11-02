# RBAC & Route Permission System (Skill Guide)

This guide documents the Role-Based Access Control (RBAC) architecture, the permission definition formula, route-level enforcement, and operational commands for the Django REST Framework backend.

## 1. Architecture Overview
The system uses a declarative, modular RBAC architecture designed for scalable Django REST Framework applications:
* **Declarative Definitions:** Each Django application declares its capability permissions in `<app>/permission.py` using a standardized formula.
* **App-Scoped Database Persistence:** The `Permission` model stores capability permissions keyed by unique `code_name`, grouped by `app_name` and `module_name`.
* **Automated Synchronization:** A management command (`sync_permissions`) scans all installed apps and upserts permissions into the database idempotently.
* **Route-Level Enforcement:** A DRF permission class (`HasPermissionCode`) inspects `action_permissions` on ViewSets and verifies against the user's assigned role.

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