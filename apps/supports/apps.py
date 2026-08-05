from django.apps import AppConfig


class SupportsConfig(AppConfig):
    name = "apps.supports"

    def ready(self) -> None:
        # FAQ 변경 시 캐시 무효화 시그널 등록
        import apps.supports.signals.signal  # noqa: F401
