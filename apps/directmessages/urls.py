from django.urls import path

from apps.directmessages.views.conversation_create_views import ConversationView
from apps.directmessages.views.message_list_views import MessageListView

app_name = "directmessages"

urlpatterns = [
    path("conversations/", ConversationView.as_view(), name="conversation-create"),
    path(
        "conversations/<str:conversation_id>/messages/",
        MessageListView.as_view(),
        name="message-list",
    ),
]
