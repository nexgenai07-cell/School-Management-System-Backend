from rest_framework import serializers

from accounts.models import User

from communication.models import Message

class ConversationContactSerializer(serializers.ModelSerializer):
    """
    Sirf naam aur id — Teacher ya Parent ki conversations list ke liye.
    GET /api/teacher/messages/conversations
    GET /api/parent/messages/conversations
    """
    class Meta:
        model = User
        fields = ["id", "full_name"]


class MessageSerializer(serializers.ModelSerializer):
    """
    Ek message ka poora data — thread view ke liye.
    sender_name aur receiver_name read-only extra fields hain.
    """
    sender_name = serializers.CharField(
        source="sender.full_name", read_only=True
    )
    receiver_name = serializers.CharField(
        source="receiver.full_name", read_only=True
    )

    class Meta:
        model = Message
        fields = [
            "id",
            "sender", "sender_name",
            "receiver", "receiver_name",
            "content",
            "is_read",
            "created_at",
        ]
        read_only_fields = [
            "sender", "sender_name",
            "receiver", "receiver_name",
            "is_read", "created_at",
        ]

    def validate_content(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Message cannot be empty.")
        return value.strip()