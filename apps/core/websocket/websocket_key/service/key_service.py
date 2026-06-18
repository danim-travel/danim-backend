import uuid

from django.core.cache import cache


def make_socket_key(user):
    socket_key = uuid.uuid4()
    cache.set(f"socket_key_{socket_key}", user.id, timeout=30)
    return socket_key
