from rest_framework.views import APIView
from apps.posts.services.sitemap_service import SitemapService
from apps.posts.serializers.sitemap_serializer import SitemapSerializer
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework import status

class SitemapView(APIView):
    permission_classes=[AllowAny]
    service = SitemapService()

    def get(self,request:Request)->Response:
        
        posts = self.service.get_sitemap_posts()
        serializer = SitemapSerializer(posts,many=True)
        return Response(serializer.data,status=status.HTTP_200_OK)
