from apps.posts.models import Post
from apps.posts.near_postspot.services import get_postspot_list, get_spots
from tests.test_core.bases.near_postspot_base import NearPostSpotBase


class TestGetSpots(NearPostSpotBase):

    def test_returns_spots_and_post_id(self):
        """게시글에 스팟이 있으면 해당 스팟들과 post_id를 반환한다"""
        spots, post_id = get_spots({"post_id": self.post_user1.id})
        self.assertEqual(post_id, self.post_user1.id)
        self.assertEqual(list(spots), [self.postspot_user1])

    def test_returns_none_when_no_spots(self):
        """게시글에 스팟이 하나도 없으면 (None, post_id)를 반환한다"""
        empty_post = Post.objects.create(user=self.user1, title="empty")
        spots, post_id = get_spots({"post_id": empty_post.id})
        self.assertIsNone(spots)
        self.assertEqual(post_id, empty_post.id)


class TestGetPostspotList(NearPostSpotBase):

    def test_empty_dict_when_spots_none(self):
        """spots가 None이면 near_spots가 빈 리스트인 dict를 반환한다"""
        result = get_postspot_list(None, "some-post-id")
        self.assertEqual(result, {"post_id": "some-post-id", "near_spots": []})

    def test_own_post_spots_excluded(self):
        """조회 대상 게시글 자신의 스팟은 근처 목록에서 제외된다.

        자기 좌표를 기준으로 검색하므로 제외하지 않으면 자기 스팟이 거리 0으로 항상
        포함되어 다른 게시글 자리를 잠식한다.
        """
        target_post, _, spot_a, _ = self._create_spot(10.000, 20.000, self.user1)
        _, _, spot_b, _ = self._create_spot(10.005, 20.000, self.user1, post=target_post)
        _, _, other_spot, _ = self._create_spot(10.010, 20.000, self.user2)

        spots, post_id = get_spots({"post_id": target_post.id})
        result = get_postspot_list(spots, post_id)

        near_ids = [s.id for g in result["near_spots"] for s in g["top_near"]]
        self.assertNotIn(spot_a.id, near_ids)
        self.assertNotIn(spot_b.id, near_ids)
        self.assertIn(other_spot.id, near_ids)

    def test_groups_near_spots_by_own_spot(self):
        """게시글의 스팟마다 근처 스팟을 조회해 spot_id 기준으로 묶어 반환한다"""
        target_post, _, spot_a, _ = self._create_spot(10.000, 20.000, self.user1)
        _, _, spot_b, _ = self._create_spot(50.000, 60.000, self.user1, post=target_post)
        _, _, near_a, _ = self._create_spot(10.005, 20.000, self.user2)

        spots, post_id = get_spots({"post_id": target_post.id})
        result = get_postspot_list(spots, post_id)

        self.assertEqual(result["post_id"], target_post.id)
        self.assertEqual(len(result["near_spots"]), 2)

        by_spot = {
            g["spot_id"]: [s.id for s in g["top_near"]] for g in result["near_spots"]
        }
        self.assertIn(near_a.id, by_spot[spot_a.id])
        self.assertNotIn(near_a.id, by_spot[spot_b.id])

    def test_duplicate_near_spot_kept_for_each_origin_spot(self):
        """같은 근처 스팟이 여러 own-spot 반경에 겹치면 중복 제거 없이 각각 포함된다"""
        target_post, _, spot_a, _ = self._create_spot(10.000, 20.000, self.user1)
        _, _, spot_b, _ = self._create_spot(10.010, 20.000, self.user1, post=target_post)
        _, _, shared_near, _ = self._create_spot(10.005, 20.000, self.user2)

        spots, post_id = get_spots({"post_id": target_post.id})
        result = get_postspot_list(spots, post_id)

        by_spot = {
            g["spot_id"]: [s.id for s in g["top_near"]] for g in result["near_spots"]
        }
        self.assertIn(shared_near.id, by_spot[spot_a.id])
        self.assertIn(shared_near.id, by_spot[spot_b.id])
