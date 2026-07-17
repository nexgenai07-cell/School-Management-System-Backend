from rest_framework import viewsets, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from accounts.permissions import IsParent
from accounts.models import ParentStudentLink
from chat.models import ChatSession, ChatMessage
from chat.serializers.parent import (
    ParentChatSessionSerializer,
    ParentChatMessageSerializer,
)

# AI service disabled in this project version


class ParentChatSessionViewSet(viewsets.ModelViewSet):
    """Parents can create and view their own chat sessions, scoped to a child."""

    serializer_class = ParentChatSessionSerializer
    permission_classes = [IsParent]

    def get_queryset(self):
        return ChatSession.objects.filter(user=self.request.user).order_by("-created_at")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ParentChatMessageViewSet(viewsets.ModelViewSet):
    """Parents can send messages. AI reply is disabled in this project version."""

    serializer_class = ParentChatMessageSerializer
    permission_classes = [IsParent]

    def get_queryset(self):
        return ChatMessage.objects.filter(session__user=self.request.user).order_by("created_at")

    def _resolve_active_child(self, child_id):
        parent_profile = getattr(self.request.user, "parent_profile", None)
        if not parent_profile:
            raise ValidationError({"child_id": "Parent profile is not available."})

        linked_child_ids = set(
            ParentStudentLink.objects.filter(parent=parent_profile).values_list("student_id", flat=True)
        )
        if child_id is None:
            return None

        try:
            child_id_int = int(child_id)
        except (TypeError, ValueError):
            raise ValidationError({"child_id": "child_id must be an integer."})

        if child_id_int not in linked_child_ids:
            raise ValidationError({"child_id": "This child is not linked to your parent account."})

        return child_id_int

    def create(self, request, *args, **kwargs):
        session_id = request.data.get("session")
        if not session_id:
            raise ValidationError({"session": "This field is required."})

        # Ensure session belongs to this parent
        session = get_object_or_404(ChatSession, id=session_id, user=request.user)

        # Optional: set active child on session for parent-scoped context
        child_id = request.data.get("child_id")
        if child_id is not None:
            resolved_child_id = self._resolve_active_child(child_id)
            session.active_child_id = resolved_child_id
            session.save(update_fields=["active_child_id"])

        content = request.data.get("content", "")
        if not content.strip():
            raise ValidationError({"content": "Message cannot be empty."})

        # Save parent message
        user_msg = ChatMessage.objects.create(session=session, role="user", content=content)

        # AI service disabled in this project version
        ai_payload = {}
        ai_text = "Sorry, abhi AI service temporarily unavailable hai. Thodi der baad try karein."

        # Save AI reply
        ai_msg = ChatMessage.objects.create(session=session, role="assistant", content=ai_text)

        serializer = self.get_serializer([user_msg, ai_msg], many=True)
        return Response(
            {
                "messages": serializer.data,
                "assistant_reply": ai_text,
                "assistant_payload": ai_payload,
                "assistant_sender_role": ai_payload.get("sender_role"),
                "assistant_sender_name": ai_payload.get("sender_name"),
            },
            status=status.HTTP_201_CREATED,
        )
