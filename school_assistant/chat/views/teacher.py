from rest_framework import viewsets, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from accounts.permissions import IsTeacher
from chat.models import ChatSession, ChatMessage
from chat.serializers.teacher import TeacherChatSessionSerializer, TeacherChatMessageSerializer
from chat.ai_service import get_ai_response


class TeacherChatSessionViewSet(viewsets.ModelViewSet):
    """Teachers can create and view their own chat sessions."""
    serializer_class = TeacherChatSessionSerializer
    permission_classes = [IsTeacher]

    def get_queryset(self):
        return ChatSession.objects.filter(user=self.request.user).order_by("-created_at")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user, bot_type="general")


class TeacherChatMessageViewSet(viewsets.ModelViewSet):
    """Teachers can send messages -- saves it AND gets back an AI reply."""
    serializer_class = TeacherChatMessageSerializer
    permission_classes = [IsTeacher]

    def get_queryset(self):
        return ChatMessage.objects.filter(session__user=self.request.user).order_by("created_at")

    def create(self, request, *args, **kwargs):
        session_id = request.data.get("session")
        if not session_id:
            raise ValidationError({"session": "This field is required."})

        session = get_object_or_404(ChatSession, id=session_id, user=request.user)
        content = request.data.get("content", "")

        user_msg = ChatMessage.objects.create(session=session, role="user", content=content)
        ai_payload = get_ai_response(user=request.user, session=session, user_message=content)
        ai_text = ai_payload.get("reply", "")
        ai_msg = ChatMessage.objects.create(session=session, role="assistant", content=ai_text)

        serializer = self.get_serializer([user_msg, ai_msg], many=True)
        return Response(
            {
                "messages": serializer.data,
                "assistant_reply": ai_text,
                "assistant_payload": ai_payload,
            },
            status=status.HTTP_201_CREATED,
        )
