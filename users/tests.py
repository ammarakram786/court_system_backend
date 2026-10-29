from django.test import TestCase
from users.models import User, Role, Permission
from users.services import user_create, role_create
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
