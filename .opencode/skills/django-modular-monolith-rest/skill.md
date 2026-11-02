---
name: django-modular-monolith-rest
description: Skill for building and modifying Django + Django REST Framework applications as modular monoliths where each Django app is a bounded module and every concrete model lives in its own file inside the app's models package.
---

# Django Modular Monolith REST Skill

Use this skill when creating, modifying, refactoring, or reviewing a Django + DRF backend that follows a **modular monolithic architecture** and uses **one model per file inside each app’s `models/` package**.

This skill is intended for AI coding agents and human developers.

---

## 1. Primary Goal

Build Django applications as clean, modular, vertically bounded modules inside a single deployable monolith.

Each Django app should represent one business module or bounded context, for example:

```text
accounts
etc
```

Each module should own its own:

- models
- serializers
- views
- URLs
- services
- selectors
- permissions
- tests
- admin configuration, if needed

The application remains a monolith, but modules should have strong internal cohesion and loose coupling between modules.

---

## 2. Non-Negotiable Rules

### 2.1 One concrete model per file

Every concrete Django model must live in its own file inside the app’s `models/` package.

Correct:

```text
apps/cases/models/case.py
apps/cases/models/hearing.py
apps/cases/models/evidence.py
```

Incorrect:

```text
apps/cases/models/cases_and_hearings.py
apps/cases/models/misc.py
apps/cases/models.py
```

If the project currently uses a single `models.py`, refactor it into a `models/` package with one file per model.

---

### 2.2 Use a `models/` package, not a single `models.py`

Django apps should use:

```text
<app>/models/__init__.py
<app>/models/<model_name>.py
```

The `__init__.py` file must import every model so Django can discover them.

Example:

```text
apps/cases/models/
├── __init__.py
├── case.py
├── hearing.py
└── evidence.py
```

---

### 2.3 File names must match model names in snake_case

For a model named `Case`, use:

```text
case.py
```

For a model named `CaseDocument`, use:

```text
case_document.py
```

For a model named `HearingOutcome`, use:

```text
hearing_outcome.py
```

---

### 2.4 Export all models from `models/__init__.py`

Example:

```text
from .case import Case
from .evidence import Evidence
from .hearing import Hearing

__all__ = [
    "Case",
    "Evidence",
    "Hearing",
]
```

This allows imports like:

```text
from apps.cases.models import Case
```

Do not force consumers to import from private model files unless necessary.

---

### 2.5 Each Django app must be a modular monolith module

Each app should encapsulate its own domain behavior.

A module should expose behavior through:

- services
- selectors
- serializers
- views
- URLs
- permissions

Other modules should avoid reaching deeply into another module’s internals.

Prefer:

```text
from apps.cases.services import close_case
from apps.cases.selectors import get_case_by_id
```

Over:

```text
from apps.cases.models.case import Case
case = Case.objects.get(id=case_id)
case.status = "closed"
case.save()
```

Direct model access may be acceptable inside the same module. Across modules, prefer the owning module’s public service or selector layer.

---

## 3. Recommended Project Structure

Use an `apps/` directory for Django modules.

```text
project_root/
├── manage.py
├── config/
│   ├── __init__.py
│   ├── settings/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── development.py
│   │   └── production.py
│   ├── urls.py
│   ├── celery.py
│   └── wsgi.py
├── apps/
│   ├── accounts/
│   │   ├── __init__.py
│   │   ├── apps.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── role.py
│   │   │   ├── permission.py
│   │   │   └── organization.py
│   │   ├── serializers/
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── role.py
│   │   │   └── organization.py
│   │   ├── views/
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── role.py
│   │   │   └── organization.py
│   │   ├── services.py
│   │   ├── selectors.py
│   │   ├── permission.py
│   │   ├── permissions.py
│   │   ├── urls.py
│   │   ├── admin.py
│   │   └── tests/
│   │       ├── __init__.py
│   │       ├── test_models.py
│   │       ├── test_services.py
│   │       └── test_api.py
│------etc
└── common/
    ├── __init__.py
    ├── models.py
    ├── exceptions.py
    ├── pagination.py
    └── permissions.py
```

---

## 4. App Configuration Template

Each app should define an `AppConfig`.

Example for `apps/cases/apps.py`:

```text
from django.apps import AppConfig


class CasesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.cases"
    label = "cases"
    verbose_name = "Cases"
```

Important:

- `name` should be the full text path: `"apps.cases"`
- `label` should be the short app label: `"cases"`

Register the app in settings using the full path:

```text
INSTALLED_APPS = [
    # Django apps
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Third-party apps
    "rest_framework",

    # Local modules
    "apps.accounts",
    "apps.cases",
]
```

---

## 5. Model Package Rules


## Non-Negotiable Rule: Choice Fields Must Be Integer Fields

All model fields that represent a fixed set of choices must use an integer-based field.

Use:

```text
models.IntegerField

### 5.1 Example model file

`apps/cases/models/case.py`:

```



```text
import uuid

from django.db import models


class Case(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "cases"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.title
```

---

### 5.2 Export the model

`apps/cases/models/__init__.py`:

```text
from .case import Case
from .evidence import Evidence
from .hearing import Hearing

__all__ = [
    "Case",
    "Evidence",
    "Hearing",
]
```

---

### 5.3 Abstract base models

Shared abstract base models may live in a common location.

Example:

```text
common/models.py
```

```text
import uuid

from django.db import models


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class UUIDModel(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    class Meta:
        abstract = True
```

Concrete domain models must still have their own file.

Example:

```text
from django.db import models

from common.models import TimeStampedModel, UUIDModel


class Case(UUIDModel, TimeStampedModel):
    title = models.CharField(max_length=255)

    class Meta:
        app_label = "cases"

    def __str__(self) -> str:
        return self.title
```

---

## 6. Modular Monolith Dependency Rules

### 6.1 Module ownership

Each module owns its data and business rules.

For example:

```text
accounts owns users, roles, permissions, organizations
cases owns cases, hearings, evidence
documents owns documents, uploads, metadata
```

---

### 6.2 Allowed imports

Inside a module, imports should generally be from:

- text standard library
- Django
- third-party libraries
- shared/common kernel
- the same module

Example inside `apps/cases/services.py`:

```text
from apps.cases.models import Case
from apps.cases.selectors import get_case_by_id
```

---

### 6.3 Cross-module access

When one module needs behavior from another module, prefer the other module’s public functions.

Prefer:

```text
from apps.accounts.services import get_user_by_id
```

Over directly querying another module’s models from inside business logic:

```text
from apps.accounts.models import User
user = User.objects.get(id=user_id)
```

Direct model imports across modules may be acceptable in serializers, admin, or migrations, but business logic should stay inside the owning module.

---

### 6.4 Avoid circular dependencies

Do not create circular imports between modules.

If two modules need each other:

1. move shared logic to a common module,
2. introduce an explicit service boundary,
3. use Django signals/events, or
4. refactor the bounded contexts.

---

### 6.5 Foreign keys across modules

If a model in one module references a model in another module, prefer string references where practical.

Example:

```text
class Evidence(models.Model):
    case = models.ForeignKey(
        "cases.Case",
        on_delete=models.CASCADE,
        related_name="evidence_items",
    )
```

If referencing `accounts.User`:

```text
from django.conf import settings


class Case(models.Model):
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_cases",
    )
```

---

## 7. Service Layer Rules

Use services for commands and state-changing operations.

Services should:

- create, update, delete, or transition domain objects
- enforce business rules
- coordinate multiple models if needed
- raise domain exceptions when invalid

Example:

`apps/cases/services.py`:

```text
from apps.cases.models import Case


def create_case(*, title: str, description: str = "") -> Case:
    return Case.objects.create(
        title=title,
        description=description,
    )


def close_case(*, case: Case) -> Case:
    case.status = Case.Status.CLOSED
    case.save(update_fields=["status", "updated_at"])
    return case
```

Views should call services, not contain business logic.

---

## 8. Selector Layer Rules

Use selectors for read/query operations.

Example:

`apps/cases/selectors.py`:

```text
from apps.cases.models import Case


def get_case_by_id(*, case_id) -> Case:
    return Case.objects.get(case_id=case_id)


def list_cases(*, status: str | None = None):
    queryset = Case.objects.all()

    if status:
        queryset = queryset.filter(status=status)

    return queryset.order_by("-created_at")
```

---

## 9. DRF REST Rules

### 9.1 Use ViewSets for resources

Each primary resource should usually have its own ViewSet.

Example:

`apps/cases/views/case.py`:

```text
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from apps.cases.models import Case
from apps.cases.selectors import list_cases
from apps.cases.serializers.case import CaseSerializer
from apps.cases.services import create_case


class CaseViewSet(viewsets.ModelViewSet):
    serializer_class = CaseSerializer
    permission_classes = [IsAuthenticated]
    queryset = Case.objects.all()

    def get_queryset(self):
        return list_cases(status=self.request.query_params.get("status"))
```

If the project uses RBAC permissions, attach them according to the RBAC skill.

---

### 9.2 Keep views thin

Views should:

- validate input through serializers
- call services or selectors
- return serialized responses

Views should not:

- contain complex business rules
- perform many unrelated model mutations
- directly send emails, call external APIs, or coordinate side effects unless delegated to services

---

### 9.3 URLs belong to the module

`apps/cases/urls.py`:

```text
from rest_framework.routers import DefaultRouter

from apps.cases.views.case import CaseViewSet
from apps.cases.views.evidence import EvidenceViewSet
from apps.cases.views.hearing import HearingViewSet

router = DefaultRouter()
router.register(prefix="cases", viewset=CaseViewSet, basename="case")
router.register(prefix="hearings", viewset=HearingViewSet, basename="hearing")
router.register(prefix="evidence", viewset=EvidenceViewSet, basename="evidence")

urlpatterns = router.urls
```

Root URL configuration:

```text
from django.urls import include, path

urlpatterns = [
    path("api/v1/accounts/", include("apps.accounts.urls")),
    path("api/v1/cases/", include("apps.cases.urls")),
]
```

---

## 10. Serializer Rules

Prefer one serializer file per model/resource.

Example:

```text
apps/cases/serializers/case.py
apps/cases/serializers/hearing.py
apps/cases/serializers/evidence.py
```

Example serializer:

```text
from rest_framework import serializers

from apps.cases.models import Case


class CaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Case
        fields = [
            "case_id",
            "title",
            "description",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "case_id",
            "created_at",
            "updated_at",
        ]
```

Export serializers from `serializers/__init__.py`:

```text
from .case import CaseSerializer

__all__ = [
    "CaseSerializer",
]
```

---

## 11. RBAC Permission Integration

If the project uses the RBAC permission system, each module should declare its permissions in its own `permission.py` file.

Example:

`apps/cases/permission.py`:

```text
from accounts.models import Permission

PERMISSIONS = [
    Permission(
        name="Create Case",
        code_name="case_create",
        module_name="Case",
        app_name="cases",
        description="User can create cases",
    ),
    Permission(
        name="Read Case",
        code_name="case_read",
        module_name="Case",
        app_name="cases",
        description="User can read cases",
    ),
    Permission(
        name="Update Case",
        code_name="case_update",
        module_name="Case",
        app_name="cases",
        description="User can update cases",
    ),
    Permission(
        name="Delete Case",
        code_name="case_delete",
        module_name="Case",
        app_name="cases",
        description="User can delete cases",
    ),
]
```

For an existing `permission.py`, append using:

```text
PERMISSIONS += [
    ...
]
```

Then synchronize:

```bash
text manage.py sync_permissions
```

Protect ViewSets:

```text
from rest_framework.permissions import IsAuthenticated
from rest_framework import viewsets

from accounts.permissions import HasPermissionCode


class CaseViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, HasPermissionCode]
    permission_prefix = "case"
    action_permissions = {
        "list": "case_read",
        "retrieve": "case_read",
        "create": "case_create",
        "update": "case_update",
        "partial_update": "case_update",
        "destroy": "case_delete",
    }
```

Unless explicitly requested by the user, do not introduce permission overrides.

---

## 12. Admin Rules

Use one admin file per app unless the app becomes very large.

If the app becomes large, split admin into an `admin/` package:

```text
apps/cases/admin/
├── __init__.py
├── case.py
├── hearing.py
└── evidence.py
```

Simple example:

```text
from django.contrib import admin

from apps.cases.models import Case


@admin.register(Case)
class CaseAdmin(admin.ModelAdmin):
    list_display = [
        "case_id",
        "title",
        "status",
        "created_at",
        "updated_at",
    ]
    search_fields = [
        "title",
    ]
    list_filter = [
        "status",
    ]
```

---

## 13. Testing Rules

Each module should have tests for:

- models
- services
- selectors
- API endpoints

Recommended structure:

```text
apps/cases/tests/
├── __init__.py
├── test_models.py
├── test_services.py
├── test_selectors.py
└── test_api.py
```

Minimum expectations:

- model creation works
- model constraints are enforced
- service functions enforce business rules
- API returns `200`/`201` for authorized users
- API returns `403` for unauthorized users if RBAC is enabled
- API returns `400` for invalid payloads

---

## 14. Agent Workflow

When asked to add a new model, feature, or module, follow this order.

### Step 1: Identify the module

Determine the bounded context.

Examples:

```text
User, Role, Permission -> accounts
Case, Hearing, Evidence -> cases
Document, Attachment -> documents
```

If the model belongs to a new bounded context, create a new Django app.

---

### Step 2: Create or update the app package

For a new app:

```text
apps/<module_name>/
├── __init__.py
├── apps.py
├── models/
│   └── __init__.py
├── serializers/
│   └── __init__.py
├── views/
│   └── __init__.py
├── services.py
├── selectors.py
├── permission.py
├── urls.py
├── admin.py
└── tests/
    └── __init__.py
```

Register the app in settings.

---

### Step 3: Create one model file per model

Create:

```text
apps/<module>/models/<model_name>.py
```

Use snake_case file names.

---

### Step 4: Export models from `models/__init__.py`

Update:

```text
apps/<module>/models/__init__.py
```

Import and export every concrete model.

---

### Step 5: Create migrations

Run:

```bash
text manage.py makemigrations <app_label>
```

Example:

```bash
text manage.py makemigrations cases
```

Then:

```bash
text manage.py migrate
```

---

### Step 6: Add serializers

Create:

```text
apps/<module>/serializers/<model_name>.py
```

Export from:

```text
apps/<module>/serializers/__init__.py
```

---

### Step 7: Add services and selectors

Use:

```text
apps/<module>/services.py
apps/<module>/selectors.py
```

Services for mutations.

Selectors for queries.

---

### Step 8: Add ViewSet and URLs

Create:

```text
apps/<module>/views/<model_name>.py
```

Register the ViewSet in:

```text
apps/<module>/urls.py
```

Include the module URLs in the root URL configuration.

---

### Step 9: Add RBAC permissions if required

Declare permissions in:

```text
apps/<module>/permission.py
```

Then run:

```bash
text manage.py sync_permissions
```

Protect routes using:

```text
permission_classes = [IsAuthenticated, HasPermissionCode]
```

---

### Step 10: Add tests

Add tests for:

- model creation
- service behavior
- selector filtering
- API success cases
- API authorization failures

---

## 15. Refactoring Rules

If an existing app uses `models.py`, refactor it into a package.

Before:

```text
apps/cases/models.py
```

After:

```text
apps/cases/models/
├── __init__.py
├── case.py
├── hearing.py
└── evidence.py
```

When refactoring:

1. create the `models/` package,
2. move each model into its own file,
3. export all models from `models/__init__.py`,
4. update imports if necessary,
5. ensure migrations still reference the same app label and model names,
6. run tests,
7. run `makemigrations --check` to confirm no unexpected migration changes.

Do not rename model tables or app labels during refactor unless explicitly requested.

---

## 16. Naming Conventions

### Models

```text
class Case(models.Model):
    ...
```

File:

```text
case.py
```

---

### Model files

Use singular snake_case:

```text
case.py
hearing.py
evidence_item.py
case_document.py
```

---

### ViewSets

```text
class CaseViewSet(viewsets.ModelViewSet):
    ...
```

File:

```text
views/case.py
```

---

### Serializers

```text
class CaseSerializer(serializers.ModelSerializer):
    ...
```

File:

```text
serializers/case.py
```

---

### Services

Use verb-first function names:

```text
create_case()
update_case()
close_case()
assign_hearing()
upload_document()
```

---

### Selectors

Use query-style names:

```text
get_case_by_id()
list_cases()
list_hearings_for_case()
get_document_or_404()
```

---

## 17. Acceptance Checklist

Before considering a task complete, verify:

- [ ] The app is registered in `INSTALLED_APPS`.
- [ ] The app uses a `models/` package.
- [ ] Every concrete model has its own file.
- [ ] Model file names use snake_case.
- [ ] All models are exported from `models/__init__.py`.
- [ ] No concrete domain models are hidden in `misc.py`, `common.py`, or a single `models.py`.
- [ ] Serializers exist for API-exposed models.
- [ ] Views are thin and delegate to services/selectors.
- [ ] Business logic lives in services, not views.
- [ ] Query logic lives in selectors.
- [ ] URLs are defined inside the module.
- [ ] RBAC permissions are declared if the endpoint is protected.
- [ ] `text manage.py makemigrations` succeeds.
- [ ] `text manage.py migrate` succeeds.
- [ ] Tests exist for models, services, and API behavior.
- [ ] No circular imports were introduced.
- [ ] Cross-module access respects module boundaries.

---

## 18. Example Task: Add `Document` to `documents` module

### 18.1 Create model file

`apps/documents/models/document.py`:

```text
import uuid

from django.conf import settings
from django.db import models


class Document(models.Model):
    document_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to="documents/")
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="uploaded_documents",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "documents"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.title
```

---

### 18.2 Export model

`apps/documents/models/__init__.py`:

```text
from .document import Document

__all__ = [
    "Document",
]
```

---

### 18.3 Add serializer

`apps/documents/serializers/document.py`:

```text
from rest_framework import serializers

from apps.documents.models import Document


class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = [
            "document_id",
            "title",
            "file",
            "uploaded_by",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "document_id",
            "uploaded_by",
            "created_at",
            "updated_at",
        ]
```

---

### 18.4 Add service

`apps/documents/services.py`:

```text
from apps.documents.models import Document


def create_document(*, title: str, file, uploaded_by) -> Document:
    return Document.objects.create(
        title=title,
        file=file,
        uploaded_by=uploaded_by,
    )
```

---

### 18.5 Add selector

`apps/documents/selectors.py`:

```text
from apps.documents.models import Document


def list_documents(*, uploaded_by=None):
    queryset = Document.objects.all()

    if uploaded_by:
        queryset = queryset.filter(uploaded_by=uploaded_by)

    return queryset.order_by("-created_at")
```

---

### 18.6 Add ViewSet

`apps/documents/views/document.py`:

```text
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from apps.documents.models import Document
from apps.documents.selectors import list_documents
from apps.documents.serializers.document import DocumentSerializer


class DocumentViewSet(viewsets.ModelViewSet):
    serializer_class = DocumentSerializer
    permission_classes = [IsAuthenticated]
    queryset = Document.objects.all()

    def get_queryset(self):
        return list_documents()
```

If RBAC is enabled:

```text
from accounts.permissions import HasPermissionCode


class DocumentViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, HasPermissionCode]
    permission_prefix = "document"
    action_permissions = {
        "list": "document_read",
        "retrieve": "document_read",
        "create": "document_create",
        "update": "document_update",
        "partial_update": "document_update",
        "destroy": "document_delete",
    }
```

---

### 18.7 Add module URLs

`apps/documents/urls.py`:

```text
from rest_framework.routers import DefaultRouter

from apps.documents.views.document import DocumentViewSet

router = DefaultRouter()
router.register(prefix="documents", viewset=DocumentViewSet, basename="document")

urlpatterns = router.urls
```

---

### 18.8 Add permissions

`apps/documents/permission.py`:

```text
from accounts.models import Permission

PERMISSIONS = [
    Permission(
        name="Create Document",
        code_name="document_create",
        module_name="Document",
        app_name="documents",
        description="User can create documents",
    ),
    Permission(
        name="Read Document",
        code_name="document_read",
        module_name="Document",
        app_name="documents",
        description="User can read documents",
    ),
    Permission(
        name="Update Document",
        code_name="document_update",
        module_name="Document",
        app_name="documents",
        description="User can update documents",
    ),
    Permission(
        name="Delete Document",
        code_name="document_delete",
        module_name="Document",
        app_name="documents",
        description="User can delete documents",
    ),
]
```

Sync:

```bash
text manage.py sync_permissions
```

---

## 19. Final Agent Instruction

When implementing any Django + DRF feature under this skill:

1. Treat each Django app as a bounded module.
2. Keep the monolith deployable as one unit.
3. Place every concrete model in its own file inside `models/`.
4. Export all models from `models/__init__.py`.
5. Keep views thin.
6. Put mutations in services.
7. Put reads in selectors.
8. Keep module APIs explicit.
9. Avoid cross-module business logic sprawl.
10. Add tests before considering the task complete.