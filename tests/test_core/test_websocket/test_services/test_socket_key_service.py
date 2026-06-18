from django.core.cache import cache

from apps.core.websocket.websocket_key.service import make_socket_key
from tests.test_core.test_websocket.core import SocketBaseTest


class TestSocketService(SocketBaseTest):

    def test_create_socket_key(self):
        """유저의 socket_key 생성 성공 테스트"""
        result = make_socket_key(self.user_1)
        self.assertEqual(cache.get(f"socket_key_{result}"), self.user_1.id)
