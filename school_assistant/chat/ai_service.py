"""
AI ASSISTANT SERVICE
=====================
Role-scoped context is collected from the database, then a natural-language
reply and a structured JSON payload are returned for the frontend.
"""

from datetime import datetime, timezone
import json

from django.conf import settings
import requests


# OpenRouter config
OPENROUTER_API_KEY = (
    getattr(settings, "OPENROUTER_API_KEY", "")
    or getattr(settings, "openrouter_key", "")
)
OPENROUTER_BASE_URL = getattr(settings, "OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
OPENROUTER_MODEL = getattr(settings, "OPENROUTER_MODEL", "openai/gpt-3.5-turbo")


def _call_openrouter(prompt: str) -> str:
    if not OPENROUTER_API_KEY:
        raise RuntimeError("OPENROUTER_API_KEY missing")

    url = f"{OPENROUTER_BASE_URL}/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": OPENROUTER_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2,
    }

    r = requests.post(url, headers=headers, data=json.dumps(payload), timeout=60)
    r.raise_for_status()
    data = r.json()
    return data.get("choices", [{}])[0].get("message", {}).get("content") or ""


def _format_history(session, limit=10):
    messages = session.messages.order_by("-created_at")[:limit]
    lines = []
    for m in reversed(list(messages)):
        speaker = "User" if m.role == "user" else "Assistant"
        lines.append(f"{speaker}: {m.content}")
    return "\n".join(lines)


def _safe_count(qs, default=0):
    try:
        return qs.count() if qs is not None else default
    except Exception:
        return default


def _normalize_query(text):
    return (text or "").strip().lower()


def _select_relevant_context(role, user_message, context_data):
    query = _normalize_query(user_message)

    if role == "Student":
        if any(token in query for token in ["attendance", "present", "absent", "late"]):
            return {
                "student_name": context_data.get("student_name"),
                "class_section": context_data.get("class_section"),
                "attendance": context_data.get("attendance"),
            }
        if any(token in query for token in ["grade", "marks", "result", "exam"]):
            return {
                "student_name": context_data.get("student_name"),
                "recent_grades": context_data.get("recent_grades"),
            }
        if any(token in query for token in ["fee", "fees", "payment", "challan", "unpaid"]):
            return {
                "student_name": context_data.get("student_name"),
                "fees_due": context_data.get("fees_due"),
            }
        if any(token in query for token in ["assignment", "homework", "pending"]):
            return {
                "student_name": context_data.get("student_name"),
                "pending_assignments": context_data.get("pending_assignments"),
            }
        if any(token in query for token in ["class", "section"]):
            return {
                "student_name": context_data.get("student_name"),
                "class_section": context_data.get("class_section"),
            }

    elif role == "Teacher":
        if any(token in query for token in ["assignment", "homework", "due"]):
            return {
                "teacher_name": context_data.get("teacher_name"),
                "recent_assignments": context_data.get("recent_assignments"),
                "total_assignments": context_data.get("total_assignments"),
            }
        if any(token in query for token in ["grade", "marks", "exam", "result"]):
            return {
                "teacher_name": context_data.get("teacher_name"),
                "grades_this_month": context_data.get("grades_this_month"),
            }
        if any(token in query for token in ["subject", "class", "section"]):
            return {
                "teacher_name": context_data.get("teacher_name"),
                "subjects_taught": context_data.get("subjects_taught"),
            }

    elif role == "Parent":
        if any(token in query for token in ["attendance", "present", "absent"]):
            return {
                "parent_name": context_data.get("parent_name"),
                "children": [
                    {
                        "child_name": child.get("child_name"),
                        "attendance": child.get("attendance"),
                    }
                    for child in context_data.get("children", [])
                ],
            }
        if any(token in query for token in ["grade", "marks", "result", "exam", "performance"]):
            return {
                "parent_name": context_data.get("parent_name"),
                "children": [
                    {
                        "child_name": child.get("child_name"),
                        "recent_grades": child.get("recent_grades", []),
                    }
                    for child in context_data.get("children", [])
                ],
            }
        if any(token in query for token in ["fee", "fees", "payment", "challan", "unpaid"]):
            return {
                "parent_name": context_data.get("parent_name"),
                "children": [
                    {
                        "child_name": child.get("child_name"),
                        "fees_due": child.get("fees_due"),
                    }
                    for child in context_data.get("children", [])
                ],
            }
        if any(token in query for token in ["child", "children"]):
            return {
                "parent_name": context_data.get("parent_name"),
                "children": context_data.get("children", []),
            }

    return context_data


def _student_context(user):
    try:
        profile = getattr(user, "student_profile", None)
    except Exception:
        profile = None

    if not profile:
        return {
            "student_name": getattr(user, "full_name", ""),
            "status": "profile_not_found",
            "message": "Student profile not set up yet.",
        }

    records_qs = getattr(profile, "attendance_records", None)
    grades_qs = getattr(profile, "grades", None)
    fees_qs = getattr(profile, "fees", None)

    recent_records = list(records_qs.order_by("-date")[:30]) if records_qs is not None else []
    present = sum(1 for record in recent_records if getattr(record, "status", "") == "Present")
    total = len(recent_records)

    recent_grades = []
    if grades_qs is not None:
        try:
            grade_items = grades_qs.select_related("subject")[:10]
            for grade in grade_items:
                subject_name = getattr(getattr(grade, "subject", None), "subject_name", "Unknown")
                recent_grades.append(
                    {
                        "subject": subject_name,
                        "obtained_marks": getattr(grade, "obtained_marks", None),
                        "total_marks": getattr(grade, "total_marks", None),
                    }
                )
        except Exception:
            recent_grades = []

    fees_due = _safe_count(fees_qs.filter(status__in=["Unpaid", "Partial"])) if fees_qs is not None else 0

    class_section = getattr(profile, "class_section", None)
    pending_assignments = 0
    if class_section is not None and hasattr(class_section, "assignments"):
        try:
            pending_assignments = class_section.assignments.exclude(submissions__student=profile).count()
        except Exception:
            pending_assignments = 0

    return {
        "student_name": getattr(user, "full_name", ""),
        "class_section": str(class_section) if class_section else None,
        "attendance": {"present": present, "total": total},
        "recent_grades": recent_grades,
        "pending_assignments": pending_assignments,
        "fees_due": fees_due,
    }


def _teacher_context(user):
    try:
        profile = getattr(user, "teacher_profile", None)
    except Exception:
        profile = None

    if not profile:
        return {
            "teacher_name": getattr(user, "full_name", ""),
            "status": "profile_not_found",
            "message": "Teacher profile not set up yet.",
        }

    subjects_qs = getattr(profile, "subjects_taught", None)
    subjects = []
    if subjects_qs is not None:
        try:
            subject_items = subjects_qs.select_related("class_section").all()
            subjects = [
                {
                    "subject_name": getattr(subject, "subject_name", ""),
                    "class_section": str(getattr(subject, "class_section", "")),
                }
                for subject in subject_items
            ]
        except Exception:
            subjects = []

    assignments_qs = getattr(profile, "assignments_posted", None)
    recent_assignments = []
    if assignments_qs is not None:
        try:
            recent_items = assignments_qs.order_by("-created_at")[:5]
            recent_assignments = [
                {
                    "title": getattr(item, "title", ""),
                    "due_date": getattr(item, "due_date", None).strftime("%d %b") if getattr(item, "due_date", None) else None,
                }
                for item in recent_items
            ]
        except Exception:
            recent_assignments = []

    total_assignments = _safe_count(getattr(profile, "assignments_posted", None))

    grades_qs = getattr(profile, "grades_given", None)
    grades_this_month = 0
    try:
        from django.utils import timezone

        this_month_start = timezone.now().date().replace(day=1)
        if grades_qs is not None:
            grades_this_month = grades_qs.filter(exam_date__gte=this_month_start).count()
    except Exception:
        grades_this_month = 0

    return {
        "teacher_name": getattr(user, "full_name", ""),
        "subjects_taught": subjects,
        "recent_assignments": recent_assignments,
        "total_assignments": total_assignments,
        "grades_this_month": grades_this_month,
    }


def _parent_context(user, active_child=None):
    try:
        profile = getattr(user, "parent_profile", None)
    except Exception:
        profile = None

    if not profile:
        return {
            "parent_name": getattr(user, "full_name", ""),
            "status": "profile_not_found",
            "message": "Parent profile not set up yet.",
        }

    children_qs = profile.children.all()
    if active_child is not None:
        try:
            children_qs = children_qs.filter(id=active_child.id if hasattr(active_child, "id") else active_child)
        except Exception:
            pass

    children = []
    for child in children_qs:
        attendance_records_qs = getattr(child, "attendance_records", None)
        fees_qs = getattr(child, "fees", None)
        grades_qs = getattr(child, "grades", None)

        present = 0
        total = 0
        if attendance_records_qs is not None:
            try:
                records = attendance_records_qs.all()
                total = records.count()
                present = records.filter(status="Present").count()
            except Exception:
                present = 0
                total = 0

        fees_due = _safe_count(fees_qs.filter(status__in=["Unpaid", "Partial"])) if fees_qs is not None else 0

        recent_grades = []
        if grades_qs is not None:
            try:
                grade_items = grades_qs.select_related("subject")[:10]
                recent_grades = [
                    {
                        "subject": getattr(getattr(grade, "subject", None), "subject_name", "Unknown"),
                        "obtained_marks": getattr(grade, "obtained_marks", None),
                        "total_marks": getattr(grade, "total_marks", None),
                    }
                    for grade in grade_items
                ]
            except Exception:
                recent_grades = []

        children.append(
            {
                "child_name": getattr(child.user, "full_name", ""),
                "class_section": str(getattr(child, "class_section", "")),
                "attendance": {"present": present, "total": total},
                "fees_due": fees_due,
                "recent_grades": recent_grades,
            }
        )

    return {
        "parent_name": getattr(user, "full_name", ""),
        "children": children,
    }


def _fallback_reply(role, context_data, user_message):
    if role == "Student":
        return "I reviewed your student record and prepared a summary for you."
    if role == "Teacher":
        return "I reviewed your class and assignment data and prepared a summary for you."
    if role == "Parent":
        return "I reviewed your child-related records and prepared a summary for you."
    return "I prepared the latest school information for you."


def build_assistant_payload(user, session, user_message):
    role = getattr(getattr(user, "role", None), "role_name", "User")

    try:
        if role == "Student":
            context_data = _student_context(user)
        elif role == "Teacher":
            context_data = _teacher_context(user)
        elif role == "Parent":
            context_data = _parent_context(user, active_child=getattr(session, "active_child", None))
        else:
            context_data = {}
    except Exception:
        context_data = {}

    context_data = _select_relevant_context(role, user_message, context_data)

    history = _format_history(session)
    prompt = (
        f"You are a helpful school assistant for a {role}.\n"
        f"Only use the structured data below and never invent numbers.\n\n"
        f"--- Structured data ---\n{json.dumps(context_data, ensure_ascii=False, indent=2)}\n\n"
        f"--- Conversation so far ---\n{history}\n\n"
        f"User: {user_message}\nAssistant:"
    )

    try:
        reply = _call_openrouter(prompt).strip()
    except Exception:
        reply = _fallback_reply(role, context_data, user_message)

    if not reply:
        reply = _fallback_reply(role, context_data, user_message)

    return {
        "role": role,
        "reply": reply,
        "data": context_data,
        "structured_data": context_data,
        "context_summary": json.dumps(context_data, ensure_ascii=False),
        "source": "ai_service",
        "response_type": "json",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def get_ai_response(user, session, user_message):
    return build_assistant_payload(user, session, user_message)


