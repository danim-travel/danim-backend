from rest_framework import serializers, status
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory, APITestCase

from apps.core.utils.pagination import paginate
from apps.users.models import User


class _UserSerializer(serializers.Serializer):
    """테스트 전용 미니 시리얼라이저."""

    id = serializers.CharField()
    nickname = serializers.CharField()


class PaginateHelperTest(APITestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        # 15명 생성 → page_size(10) 경계 검증용
        for i in range(15):
            User.objects.create_user(
                email=f"user{i}@test.com",
                password="pw",
                nickname=f"nick{i}",
                name=f"name{i}",
                birth_day="2000-01-01",
            )

    def _build_request(self, query: str = "") -> Request:
        return Request(APIRequestFactory().get(f"/{query}"))

    def test_response_shape(self) -> None:
        """응답이 previous/next/results 형태인지"""
        response = paginate(User.objects.all(), self._build_request(), _UserSerializer)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("previous", response.data)
        self.assertIn("next", response.data)
        self.assertIn("results", response.data)

    def test_default_page_size_is_10(self) -> None:
        """기본 10개씩 잘리는지"""
        response = paginate(User.objects.all(), self._build_request(), _UserSerializer)
        self.assertEqual(len(response.data["results"]), 10)

    def test_next_exists_when_more_pages(self) -> None:
        """남은 데이터가 있으면 next가 채워지는지"""
        response = paginate(User.objects.all(), self._build_request(), _UserSerializer)
        self.assertIsNotNone(response.data["next"])

    def test_custom_page_size(self) -> None:
        """?page_size=5 로 조절되는지"""
        response = paginate(
            User.objects.all(), self._build_request("?page_size=5"), _UserSerializer
        )
        self.assertEqual(len(response.data["results"]), 5)

    def test_max_page_size_capped(self) -> None:
        """max_page_size(100) 초과 요청 시 제한되는지 (15개뿐이라 전부)"""
        response = paginate(
            User.objects.all(), self._build_request("?page_size=999"), _UserSerializer
        )
        self.assertEqual(len(response.data["results"]), 15)  # 100으로 제한 → 전체 반환

    def test_serializer_output_in_results(self) -> None:
        """시리얼라이저가 적용된 데이터가 results에 담기는지"""
        response = paginate(User.objects.all(), self._build_request(), _UserSerializer)
        first = response.data["results"][0]
        self.assertIn("nickname", first)
        self.assertNotIn("email", first)  # 시리얼라이저에 없는 필드는 제외
