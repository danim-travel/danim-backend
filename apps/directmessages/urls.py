from django.urls import path

from apps.directmessages.views.conversation_create_views import ConversationView

app_name = "directmessages"

urlpatterns = [
    path("conversations/", ConversationView.as_view(), name="conversation-create"),
]
