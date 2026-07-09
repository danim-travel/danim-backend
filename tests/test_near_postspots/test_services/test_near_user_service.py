from apps.posts.near_postspot.services import get_near_post_queryset
from tests.test_core.bases.near_postspot_base import NearPostSpotBase


class TestNearUserService(NearPostSpotBase):
    """내 위치 주변 게시글 조회 서비스 테스트.

    base에서 생성된 스팟(user1: 37.343, user2: 37.333, 경도 127.0 공통)을
    기준점(37.338, 127.0)에서 조회하면 둘 다 약 0.55km라 반경 3km 안에 든다.
    """

    def test_within_radius(self):
        """반경 3km 이내 스팟이 조회된다 (base 스팟 2개)"""
        result = get_near_post_queryset({"latitude": 37.338, "longitude": 127.0})
        self.assertEqual(len(result), 2)

    def test_outside_radius_excluded(self):
        """반경 3km 밖 스팟은 조회되지 않는다"""
        # 기준점 37.4 → base 스팟(37.343, 37.333)은 약 6~7km 밖
        result = get_near_post_queryset({"latitude": 37.4, "longitude": 127.0})
        self.assertEqual(len(result), 0)

    def test_ordered_by_distance(self):
        """가까운 순으로 정렬된다"""
        # 기준점 37.500 기준으로 거리가 확실히 다른 스팟 배치
        self._create_spot(37.520, 127.0, self.user1)  # 약 2.2km
        self._create_spot(37.505, 127.0, self.user1)  # 약 0.55km (더 가까움)

        result = list(get_near_post_queryset({"latitude": 37.5, "longitude": 127.0}))

        self.assertEqual(len(result), 2)
        # annotate된 distance가 오름차순인지 확인
        self.assertLess(result[0].distance, result[1].distance)

    def test_top_10_limit(self):
        """반경 내 스팟이 11개 이상이면 최대 10개만 반환한다"""
        # 기준점 37.6 근처에 11개 배치 (base 스팟과 겹치지 않는 위치)
        for i in range(11):
            self._create_spot(37.6 + i * 0.0005, 127.0, self.user1)

        result = get_near_post_queryset({"latitude": 37.6, "longitude": 127.0})
        self.assertEqual(len(result), 10)

    def test_empty_when_no_nearby(self):
        """주변에 스팟이 없으면 빈 결과를 반환한다"""
        # 아무 스팟도 없는 먼 좌표
        result = get_near_post_queryset({"latitude": 35.0, "longitude": 129.0})
        self.assertEqual(len(result), 0)
