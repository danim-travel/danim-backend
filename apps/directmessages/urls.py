from django.urls import path

from apps.directmessages.views.conversation_create_views import ConversationView
from apps.directmessages.views.delete_message_views import DeleteMessageView
from apps.directmessages.views.leave_conversation_views import LeaveConversationView
from apps.directmessages.views.message_list_views import MessageListView
from apps.directmessages.views.presigned_url_view import DMPresignedUrlView

app_name = "directmessages"

urlpatterns = [
    path("conversations", ConversationView.as_view(), name="conversations"),
    path(
        "conversations/<str:conversation_id>",
        LeaveConversationView.as_view(),
        name="leave-conversation",
    ),
    path(
        "conversations/<str:conversation_id>/messages",
        MessageListView.as_view(),
        name="message-list",
    ),
    path(
        "conversations/<str:conversation_id>/messages/presigned-url",
        DMPresignedUrlView.as_view(),
        name="dm-presigned-url",
    ),
    path(
        "conversations/<str:conversation_id>/messages/<str:message_id>",
        DeleteMessageView.as_view(),
        name="delete-message",
    ),
]
