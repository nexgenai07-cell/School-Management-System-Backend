from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from django.shortcuts import get_object_or_404

from accounts.permissions import IsStudent
from chat.models import ChatSession, ChatMessage
from chat.serializers.student import StudentChatSessionSerializer, StudentChatMessageSerializer
from chat.ai_service import get_ai_response   # 👈 AI service import

class StudentChatSessionViewSet(viewsets.ModelViewSet):
    """Students can create and view their own chat sessions."""
    serializer_class = StudentChatSessionSerializer
    permission_classes = [IsStudent]

    def get_queryset(self):
        return ChatSession.objects.filter(user=self.request.user).order_by("-created_at")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user, bot_type="general")


class StudentChatMessageViewSet(viewsets.ModelViewSet):
    """Students can send and view messages in their sessions."""
    serializer_class = StudentChatMessageSerializer
    permission_classes = [IsStudent]

    def get_queryset(self):
        return ChatMessage.objects.filter(session__user=self.request.user).order_by("created_at")

    def create(self, request, *args, **kwargs):
        session_id = request.data.get("session")
        if not session_id:
            raise ValidationError({"session": "This field is required."})

        # ✅ Ensure session belongs to this student
        session = get_object_or_404(ChatSession, id=session_id, user=request.user)
        content = request.data.get("content", "")

        # ✅ Save user message
        user_msg = ChatMessage.objects.create(session=session, role="user", content=content)

        # ✅ Call AI service and get structured payload
        ai_payload = get_ai_response(user=request.user, session=session, user_message=content)
        ai_text = ai_payload.get("reply", "")

        # ✅ Save AI response
        ai_msg = ChatMessage.objects.create(session=session, role="assistant", content=ai_text)

        # ✅ Return both messages together plus structured assistant payload
        serializer = self.get_serializer([user_msg, ai_msg], many=True)
        return Response(
            {
                "messages": serializer.data,
                "assistant_reply": ai_text,
                "assistant_payload": ai_payload,
            },
            status=status.HTTP_201_CREATED,
        )
