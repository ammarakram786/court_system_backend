from datetime import timedelta
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
from users.models import User, Role, Permission, PermissionOverride
from users.services import user_create, role_create, permission_override_create
from users.permissions import HasPermissionCode
from organizations.services import organization_create

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
        # 1. Obtain token
        login_res = self.client.post('/api/v1/auth/token/', {
            'username': 'apiofficer',
            'password': 'initialpassword123'
        })
        self.assertEqual(login_res.status_code, status.HTTP_200_OK)
        refresh_token = login_res.data['refresh']
        self.assertIn('access', login_res.data)

        # 2. Refresh token (tests rotation and blacklisting)
        refresh_res = self.client.post('/api/v1/auth/token/refresh/', {
            'refresh': refresh_token
        })
        self.assertEqual(refresh_res.status_code, status.HTTP_200_OK)
        new_access = refresh_res.data['access']
        new_refresh = refresh_res.data.get('refresh')
        self.assertIsNotNone(new_access)

        # 3. Old refresh token should now be blacklisted
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
        # Attempt with wrong password
        fail_res = self.client.post('/api/v1/users/change-password/', {
            'old_password': 'wrongpassword',
            'new_password': 'newsecurepassword456'
        })
        self.assertEqual(fail_res.status_code, status.HTTP_400_BAD_REQUEST)

        # Attempt with correct password
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
        self.perm_view = Permission.objects.create(code='cases.view', module='cases')
        self.perm_create = Permission.objects.create(code='cases.create', module='cases')
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
        view = type('View', (), {'required_permission': 'cases.view'})()
        self.assertTrue(self.checker.has_permission(req, view))

    def test_role_permission_missing(self):
        req = type('Request', (), {'user': self.user})()
        view = type('View', (), {'required_permission': 'cases.create'})()
        self.assertFalse(self.checker.has_permission(req, view))

    def test_permission_override_allow(self):
        # Override grants cases.create
        permission_override_create(
            user=self.user,
            permission_code='cases.create',
            effect=PermissionOverride.Effect.ALLOW,
            reason='Special duty',
            granted_by='Commander'
        )
        req = type('Request', (), {'user': self.user})()
        view = type('View', (), {'required_permission': 'cases.create'})()
        self.assertTrue(self.checker.has_permission(req, view))

    def test_permission_override_deny_precedence(self):
        # Override explicitly denies cases.view which role has
        permission_override_create(
            user=self.user,
            permission_code='cases.view',
            effect=PermissionOverride.Effect.DENY,
            reason='Suspension',
            granted_by='Commander'
        )
        req = type('Request', (), {'user': self.user})()
        view = type('View', (), {'required_permission': 'cases.view'})()
        self.assertFalse(self.checker.has_permission(req, view))

    def test_expired_override_is_ignored(self):
        past_time = timezone.now() - timedelta(days=1)
        permission_override_create(
            user=self.user,
            permission_code='cases.view',
            effect=PermissionOverride.Effect.DENY,
            reason='Temporary suspension',
            granted_by='Commander',
            expires_at=past_time
        )
        req = type('Request', (), {'user': self.user})()
        view = type('View', (), {'required_permission': 'cases.view'})()
        # Deny override has expired, so role permission applies
        self.assertTrue(self.checker.has_permission(req, view))
