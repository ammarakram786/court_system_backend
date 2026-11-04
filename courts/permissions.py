from rest_framework.permissions import BasePermission, SAFE_METHODS
from courts.models import Case


def can_user_work_on_case(user, case: Case) -> bool:
    """
    Evaluates whether the given user is authorized to perform work/mutations
    on a case or its related records (proceedings, parties, marking, closing).

    Rules:
    1. Unauthenticated users cannot work on any case.
    2. Superusers and staff have full administrative bypass.
    3. If no case officer is assigned yet, users belonging to the managing organization can work.
    4. Direct Match: The user is the active assigned_case_officer.
    5. Peer Match: The user shares the SAME appointment and SAME organization
       as the active assigned_case_officer (both appointment and organization must match).
    6. All other users have view-only access.
    """
    if not user or not user.is_authenticated:
        return False

    if user.is_superuser or user.is_staff:
        return True

    if not case.assigned_case_officer:
        return getattr(user, 'organization_id', None) == getattr(case, 'managing_organization_id', None)

    # Direct assignee
    if case.assigned_case_officer_id == user.user_id:
        return True

    # Peer with same appointment and organization
    assigned_officer = case.assigned_case_officer
    user_app_id = getattr(user, 'appointment_id', None)
    officer_app_id = getattr(assigned_officer, 'appointment_id', None)
    user_org_id = getattr(user, 'organization_id', None)
    officer_org_id = getattr(assigned_officer, 'organization_id', None)

    if (
        user_app_id is not None
        and officer_app_id is not None
        and user_app_id == officer_app_id
        and user_org_id is not None
        and officer_org_id is not None
        and user_org_id == officer_org_id
    ):
        return True

    return False


class CanWorkOnCaseOrReadOnly(BasePermission):
    """
    Object-level permission:
    - SAFE_METHODS (GET, HEAD, OPTIONS): Granted (Provides 'view-only picture').
    - NON-SAFE METHODS (POST, PUT, PATCH, DELETE): Granted only to:
      - The active assigned case officer
      - Peers with the same appointment AND organization
      - Staff / Superusers
    """
    message = "You have view-only access to this case. Only the assigned officer or an officer with the same appointment and organization can work on it."

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True

        case = obj if isinstance(obj, Case) else getattr(obj, 'case', None)
        if not case:
            return True

        return can_user_work_on_case(request.user, case)
