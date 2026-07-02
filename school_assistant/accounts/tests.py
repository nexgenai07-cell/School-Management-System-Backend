from types import SimpleNamespace

from django.test import SimpleTestCase

from accounts.permissions import get_user_profile


class RoleProfileTests(SimpleTestCase):
    def test_missing_profile_returns_none(self):
        user = SimpleNamespace(is_authenticated=True, role=SimpleNamespace(role_name="Student"))
        self.assertIsNone(get_user_profile(user, "Student"))

    def test_existing_profile_is_returned(self):
        profile = object()
        user = SimpleNamespace(is_authenticated=True, role=SimpleNamespace(role_name="Teacher"), teacher_profile=profile)
        self.assertIs(get_user_profile(user, "Teacher"), profile)
