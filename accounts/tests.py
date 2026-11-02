from datetime import date
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from rest_framework import status
from rest_framework.test import APIClient

from accounts.models import User, Permission, Organization, Rank, Appointment
from accounts.permissions import HasPermissionCode
from accounts.services import (
    user_create, role_create, organization_create, organization_update,
    rank_create, appointment_create, permissions_sync
)


class UserModelTests(TestCase):
    def setUp(self):
        self.org = organization_create(name="HQ Org", code="HQ")
        self.role = role_create(name="Admin", description="Administrator Role")

    def test_user_creation(self):
        user = user_create(
            username="testuser",
            name="Captain Test",
            svc_number="SVC-12345",
            organization=self.org,
            role=self.role,
            password="securepassword123"
        )
        self.assertEqual(user.username, "testuser")
        self.assertTrue(user.check_password("securepassword123"))
        self.assertEqual(user.organization, self.org)

    def test_superuser_creation(self):
        su = User.objects.create_superuser(
            username="rootadmin",
            svc_number="SVC-ROOT",
            password="rootpassword123",
            name="Super Admin"
        )
        self.assertTrue(su.is_superuser)
        self.assertTrue(su.is_staff)
        self.assertTrue(su.check_password("rootpassword123"))


class UserAPITests(TestCase):
    def setUp(self):
        self.org = organization_create(name="HQ Org", code="HQ")
        self.role = role_create(name="Officer")
        self.user = user_create(
            username="apiofficer",
            name="Major Officer",
            svc_number="SVC-777",
            organization=self.org,
            role=self.role,
            password="initialpassword123"
        )
        self.client = APIClient()

    def test_jwt_auth_and_token_refresh_with_blacklist(self):
        login_res = self.client.post('/api/v1/auth/token/', {
            'username': 'apiofficer',
            'password': 'initialpassword123'
        })
        self.assertEqual(login_res.status_code, status.HTTP_200_OK)
        refresh_token = login_res.data['refresh']
        self.assertIn('access', login_res.data)

        refresh_res = self.client.post('/api/v1/auth/token/refresh/', {
            'refresh': refresh_token
        })
        self.assertEqual(refresh_res.status_code, status.HTTP_200_OK)
        new_access = refresh_res.data['access']
        self.assertIsNotNone(new_access)

        failed_refresh = self.client.post('/api/v1/auth/token/refresh/', {
            'refresh': refresh_token
        })
        self.assertEqual(failed_refresh.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_me_endpoint(self):
        self.client.force_authenticate(user=self.user)
        res = self.client.get('/api/v1/users/me/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['username'], 'apiofficer')
        self.assertEqual(res.data['organization_details']['code'], 'HQ')

    def test_change_password_endpoint(self):
        self.client.force_authenticate(user=self.user)
        fail_res = self.client.post('/api/v1/users/change-password/', {
            'old_password': 'wrongpassword',
            'new_password': 'newsecurepassword456'
        })
        self.assertEqual(fail_res.status_code, status.HTTP_400_BAD_REQUEST)

        success_res = self.client.post('/api/v1/users/change-password/', {
            'old_password': 'initialpassword123',
            'new_password': 'newsecurepassword456'
        })
        self.assertEqual(success_res.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('newsecurepassword456'))


class RBACPermissionTests(TestCase):
    def setUp(self):
        self.org = organization_create(name="HQ Org", code="HQ")
        self.perm_view = Permission.objects.create(
            name='Read Cases',
            code_name='case_read',
            module_name='Case',
            app_name='courts'
        )
        self.perm_create = Permission.objects.create(
            name='Create Cases',
            code_name='case_create',
            module_name='Case',
            app_name='courts'
        )
        self.role = role_create(name="Reader", permission_ids=[self.perm_view.pk])
        self.user = user_create(
            username="reader1",
            name="Reader One",
            svc_number="SVC-R1",
            organization=self.org,
            role=self.role
        )
        self.checker = HasPermissionCode()

    def test_role_permission_granted(self):
        req = type('Request', (), {'user': self.user})()
        view = type('View', (), {'required_permission': 'case_read'})()
        self.assertTrue(self.checker.has_permission(req, view))

    def test_role_permission_missing(self):
        req = type('Request', (), {'user': self.user})()
        view = type('View', (), {'required_permission': 'case_create'})()
        self.assertFalse(self.checker.has_permission(req, view))

    def test_action_permissions_check(self):
        req = type('Request', (), {'user': self.user})()
        view = type('View', (), {
            'action': 'list',
            'action_permissions': {'list': 'case_read', 'create': 'case_create'}
        })()
        self.assertTrue(self.checker.has_permission(req, view))

        view.action = 'create'
        self.assertFalse(self.checker.has_permission(req, view))

    def test_sync_permissions(self):
        count = permissions_sync()
        self.assertGreater(count, 0)
        self.assertTrue(Permission.objects.filter(code_name='role_create').exists())
        self.assertTrue(Permission.objects.filter(code_name='court_create').exists())

    def test_route_permission_enforcement_allow_and_deny(self):
        perm_role_read, _ = Permission.objects.get_or_create(
            code_name='role_read',
            defaults={'name': 'Read Role', 'module_name': 'Role', 'app_name': 'accounts'}
        )
        perm_role_create, _ = Permission.objects.get_or_create(
            code_name='role_create',
            defaults={'name': 'Create Role', 'module_name': 'Role', 'app_name': 'accounts'}
        )
        self.role.permissions.add(perm_role_read)

        client = APIClient()
        client.force_authenticate(user=self.user)

        # 1. GET /api/v1/roles/ should succeed because user has 'role_read'
        res_get = client.get('/api/v1/roles/')
        self.assertEqual(res_get.status_code, status.HTTP_200_OK)

        # 2. POST /api/v1/roles/ should fail (403) because user lacks 'role_create'
        res_post = client.post('/api/v1/roles/', {'name': 'New Restricted Role'})
        self.assertEqual(res_post.status_code, status.HTTP_403_FORBIDDEN)

        # 3. Add override DENY for 'role_read' -> GET should now be forbidden
        from accounts.models import PermissionOverride
        PermissionOverride.objects.create(
            user=self.user,
            permission_code='role_read',
            effect='DENY',
            reason='Suspended viewing',
            granted_by='admin'
        )
        res_get_denied = client.get('/api/v1/roles/')
        self.assertEqual(res_get_denied.status_code, status.HTTP_403_FORBIDDEN)

        # 4. Add override ALLOW for 'role_create' -> POST should now succeed
        PermissionOverride.objects.create(
            user=self.user,
            permission_code='role_create',
            effect='ALLOW',
            reason='Special grant',
            granted_by='admin'
        )
        res_post_allowed = client.post('/api/v1/roles/', {'name': 'New Allowed Role'})
        self.assertEqual(res_post_allowed.status_code, status.HTTP_201_CREATED)


class OrganizationModelTests(TestCase):
    def test_single_root_organization_constraint(self):
        root1 = organization_create(name="Root HQ", code="HQ-001")
        self.assertEqual(root1.org_level, 1)
        self.assertIsNone(root1.parent_organization)
        self.assertTrue(root1.is_root)

        with self.assertRaises(ValidationError):
            organization_create(name="Second Root HQ", code="HQ-002")

    def test_sub_organization_creation(self):
        root = organization_create(name="Root HQ", code="HQ-001")
        sub1 = organization_create(parent_organization=root, name="Legal Directorate", code="LD-001")
        self.assertEqual(sub1.org_level, 2)
        self.assertEqual(sub1.parent_organization, root)
        self.assertFalse(sub1.is_root)

    def test_circular_organization_prevention(self):
        root = organization_create(name="Root HQ", code="HQ-001")
        sub1 = organization_create(parent_organization=root, name="Legal Directorate", code="LD-001")
        root.parent_organization = sub1
        with self.assertRaises(ValidationError):
            root.save()

    def test_self_parent_prevention(self):
        root = organization_create(name="Root HQ", code="HQ-001")
        root.parent_organization = root
        with self.assertRaises(ValidationError):
            root.save()


class RankAppointmentTests(TestCase):
    def test_rank_and_appointment_creation(self):
        rank = rank_create(title="Major", abbreviation="Maj", seniority_index=10)
        self.assertEqual(str(rank), "Major (Maj)")

        appt = appointment_create(title="Legal Officer", appointment_code="LO-01")
        self.assertEqual(str(appt), "Legal Officer")


class OrganizationAPITests(TestCase):
    def setUp(self):
        self.root = organization_create(name="Root HQ", code="HQ-ROOT")
        self.sub = organization_create(parent_organization=self.root, name="Sub Branch", code="HQ-SUB")
        self.role = role_create(name="Admin")
        self.user = user_create(
            username="adminuser",
            name="Admin",
            svc_number="SVC-ADMIN",
            organization=self.root,
            role=self.role,
            is_staff=True
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_root_action(self):
        response = self.client.get('/api/v1/organizations/root/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['code'], 'HQ-ROOT')
        self.assertEqual(response.data['sub_organizations_count'], 1)

    def test_sub_organizations_action(self):
        response = self.client.get(f'/api/v1/organizations/{self.root.pk}/sub-organizations/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['code'], 'HQ-SUB')
