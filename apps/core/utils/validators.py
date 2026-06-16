from rest_framework.exceptions import NotFound


def validate_ulid(value: str) -> None:
    """ULID는 항상 26자. DB 쿼리 없이 즉시 튕겨냄."""
    if len(value) != 26:
        raise NotFound()
