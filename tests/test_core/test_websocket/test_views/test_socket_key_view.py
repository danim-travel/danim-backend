from time import sleep

from django.core.cache import cache
from rest_framework import status

from tests.test_core.test_websocket.core import SocketBaseTest


class TestSocketKeyView(SocketBaseTest):

    def test_get_socket_key(self):
        """로그인 한 유저의 socket_key 발급 view 성공 테스트"""
        self.client.force_authenticate(user=self.user_1)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["socket_key"])
        socket_key = response.data["socket_key"]
        self.assertEqual(cache.get(f"socket_key_{socket_key}"), self.user_1.id)

    def test_unauthorized_socket_key(self):
        """비로그인 한 유저의 socket_key 발급 view 실패 테스트"""
        self.client.force_authenticate(user=None)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
