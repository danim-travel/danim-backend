from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.users.services.profile_service import ProfileService
from rest_framework.request import Request
from rest_framework.response import Response
from apps.users.serializers.profile_serializer import ProfileResponseSerializer

class ProfileView(APIView):
    permission_classes = [IsAuthenticated]
    service = ProfileService()

    def get(self,request:Request,user_id:str)->Response:

        user = self.service.get_profile(
            user_id=user_id,
            request_user=request.user,
            )
        return Response(
            ProfileResponseSerializer(user).data,
            status=status.HTTP_200_OK
        )