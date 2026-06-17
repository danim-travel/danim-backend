from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.websocket.websocket_key.service import make_socket_key


class WebSocketKey(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        socket_key = make_socket_key(request.user)
        return Response({"socket_key": socket_key}, status=status.HTTP_200_OK)
