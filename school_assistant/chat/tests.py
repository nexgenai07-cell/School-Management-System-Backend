from types import SimpleNamespace
from unittest.mock import patch

from unittest.mock import patch

from django.test import SimpleTestCase
from rest_framework.exceptions import ValidationError

# tests file kept but updated imports are optional; chatbot endpoints are disabled in this repo version.
# chatbot disabled: tests should not import ai_service modules
from chat.ai_service_optimized import get_ai_response

from chat.views.parent import ParentChatMessageViewSet


class AssistantPayloadTests(SimpleTestCase):
    def test_student_payload_contains_structured_data(self):
        user = SimpleNamespace(
            full_name="Ali Khan",
            role=SimpleNamespace(role_name="Student"),
        )
        profile = SimpleNamespace(
            attendance_records=SimpleNamespace(
                order_by=lambda *args, **kwargs: [
                    SimpleNamespace(status="Present"),
                    SimpleNamespace(status="Absent"),
                ]
            ),
            grades=SimpleNamespace(select_related=lambda *args, **kwargs: []),
            fees=SimpleNamespace(filter=lambda *args, **kwargs: SimpleNamespace(count=lambda: 1)),
            class_section="10-A",
        )
        user.student_profile = profile
        session = SimpleNamespace(active_child=None, messages=SimpleNamespace(order_by=lambda *args, **kwargs: []))

        with patch("chat.ai_service._call_openrouter", return_value="Your attendance looks fine"):
            payload = build_assistant_payload(user, session, "What is my attendance?")

        self.assertEqual(payload["role"], "Student")
        self.assertEqual(payload["data"]["attendance"]["present"], 1)
        self.assertEqual(payload["data"]["attendance"]["total"], 2)
        self.assertIn("reply", payload)
        self.assertIn("structured_data", payload)

    def test_attendance_query_does_not_return_unrelated_student_fields(self):
        user = SimpleNamespace(
            full_name="Ali Khan",
            role=SimpleNamespace(role_name="Student"),
        )
        profile = SimpleNamespace(
            attendance_records=SimpleNamespace(
                order_by=lambda *args, **kwargs: [
                    SimpleNamespace(status="Present"),
                    SimpleNamespace(status="Absent"),
                ]
            ),
            grades=SimpleNamespace(select_related=lambda *args, **kwargs: []),
            fees=SimpleNamespace(filter=lambda *args, **kwargs: SimpleNamespace(count=lambda: 1)),
            class_section="10-A",
        )
        user.student_profile = profile
        session = SimpleNamespace(active_child=None, messages=SimpleNamespace(order_by=lambda *args, **kwargs: []))

        with patch("chat.ai_service._call_openrouter", return_value="Attendance summary"):
            payload = build_assistant_payload(user, session, "What is my attendance today?")

        self.assertIn("attendance", payload["data"])
        self.assertNotIn("recent_grades", payload["data"])
        self.assertNotIn("fees_due", payload["data"])

    def test_parent_child_scoping_rejects_unlinked_child_ids(self):
        user = SimpleNamespace(
            full_name="Mr. Khan",
            role=SimpleNamespace(role_name="Parent"),
        )
        parent_profile = SimpleNamespace()
        user.parent_profile = parent_profile

        viewset = ParentChatMessageViewSet()
        viewset.request = SimpleNamespace(user=user)

        with patch("chat.views.parent.ParentStudentLink.objects.filter") as mock_filter:
            mock_filter.return_value.values_list.return_value = [42]
            with self.assertRaises(ValidationError):
                viewset._resolve_active_child(99)

    def test_parent_grade_query_returns_child_grade_details(self):
        user = SimpleNamespace(
            full_name="Mr. Khan",
            role=SimpleNamespace(role_name="Parent"),
        )
        child = SimpleNamespace(
            user=SimpleNamespace(full_name="Sara Khan"),
            class_section="10-A",
            attendance_records=SimpleNamespace(all=lambda: SimpleNamespace(count=lambda: 2, filter=lambda *args, **kwargs: SimpleNamespace(count=lambda: 1))),
            fees=SimpleNamespace(filter=lambda *args, **kwargs: SimpleNamespace(count=lambda: 1)),
            grades=SimpleNamespace(select_related=lambda *args, **kwargs: [
                SimpleNamespace(subject=SimpleNamespace(subject_name="Math"), obtained_marks=80, total_marks=100)
            ]),
        )
        profile = SimpleNamespace(children=SimpleNamespace(all=lambda: [child]))
        user.parent_profile = profile
        session = SimpleNamespace(active_child=None, messages=SimpleNamespace(order_by=lambda *args, **kwargs: []))

        with patch("chat.ai_service._call_openrouter", return_value="Grade summary"):
            payload = build_assistant_payload(user, session, "How did Sara perform in exams?")

        self.assertEqual(payload["role"], "Parent")
        self.assertIn("recent_grades", payload["data"]["children"][0])
        self.assertEqual(payload["data"]["children"][0]["recent_grades"][0]["subject"], "Math")
