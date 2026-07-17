from rest_framework import serializers
from chat.models import ChatSession, ChatMessage

class ParentChatSessionSerializer(serializers.ModelSerializer):
    active_child_name = serializers.CharField(source="active_child.user.full_name", read_only=True)

    class Meta:
        model = ChatSession
        fields = ["id", "title", "active_child", "active_child_name", "created_at"]


class ParentChatMessageSerializer(serializers.ModelSerializer):
    # Accept selected child for scoping AI context.
    # This is NOT stored on ChatMessage; it updates ChatSession.active_child in the view.
    child_id = serializers.IntegerField(required=False, write_only=True, allow_null=True)

    class Meta:
        model = ChatMessage
<<<<<<< HEAD
        fields = ["id", "role", "content", "created_at", "child_id"]
=======
        fields = ["id", "role", "content", "created_at"]
>>>>>>> 57c527b969d0f2f7a0f532b1c9918a8df652610d
