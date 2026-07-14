from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from django.shortcuts import get_object_or_404

from accounts.permissions import IsStudent
from chat.models import ChatSession, ChatMessage
from chat.serializers.student import StudentChatSessionSerializer, StudentChatMessageSerializer
# AI service disabled in this project version

from chat.validators import validate_message_content, validate_session_access


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
        validate_session_access(request.user, session)

        content = request.data.get("content", "")
        content = validate_message_content(content)

        # ✅ Call AI service and get structured payload (avoid 500 on OpenRouter/network issues)
        try:
            ai_payload = get_ai_response(user=request.user, session=session, user_message=content)
            ai_text = ai_payload.get("reply", "")
        except Exception:
            ai_payload = {}
            ai_text = "Sorry, abhi AI service temporarily unavailable hai. Thodi der baad try karein."


        # ✅ Save user message
        # NOTE: If AI performed a private note save action, it already created the note message.
        # To avoid double-save for the same note, skip saving the original user message in that case.
        if ai_payload.get("source") != "action_save_note":
            user_msg = ChatMessage.objects.create(session=session, role="user", content=content)
        else:
            # Create a lightweight dummy object for serializer compatibility
            user_msg = type(
                "Msg",
                (),
                {
                    "id": None,
                    "role": "user",
                    "content": content,
                    "created_at": None,
                    "session_id": session.id,
                },
            )()


        # ✅ Save AI response
        ai_msg = ChatMessage.objects.create(session=session, role="assistant", content=ai_text)

        # ✅ Return both messages together plus structured assistant payload
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
