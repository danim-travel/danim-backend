from django.test import TestCase

from apps.posts.serializers.update_serializer import PostUpdateSerializer


class PostUpdateSerializerTest(TestCase):

    def test_update_post_serializer_title_only(self) -> None:
        """title만 수정 시 성공 테스트"""
        serializer = PostUpdateSerializer(data={"title": "new_title"})
        self.assertTrue(serializer.is_valid())

    def test_update_post_serializer_all_fields(self) -> None:
        """모든 필드 수정 시 성공 테스트"""
        serializer = PostUpdateSerializer(
            data={
                "title": "new_title",
                "description": "new_description",
                "thumbnail": "local/upload/image/post/thumbnail/01JZWK7R2MNBX5QD8FHYC3VT8D.jpg",
                "thumbnail_width": 1080,
                "thumbnail_height": 1350,
                "spots": [
                    {
                        "order": 1,
                        "content": "new_content",
                        "location": {
                            "place_name": "성산일출봉",
                            "address_name": "제주특별자치도 서귀포시 성산읍 성산리 1",
                            "road_address_name": "제주특별자치도 서귀포시 성산읍 일출로 284-12",
                            "x": "126.942492",
                            "y": "33.458421",
                        },
                        "images": [
                            {
                                "original_img": "제주도1일차.png",
                                "key": "local/upload/image/post/01JZWK7R2MNBX5QD8FHYC3VT9E.jpg",
                                "width": 1080,
                                "height": 1350,
                            }
                        ],
                    }
                ],
            }
        )
        self.assertTrue(serializer.is_valid())

    def test_fail_update_post_serializer_no_fields(self) -> None:
        """아무 필드도 없을 시 실패 테스트"""
        serializer = PostUpdateSerializer(data={})
        self.assertFalse(serializer.is_valid())

    def test_fail_update_post_serializer_title_too_long(self) -> None:
        """title 100자 초과 시 실패 테스트"""
        serializer = PostUpdateSerializer(data={"title": "a" * 101})
        self.assertFalse(serializer.is_valid())

    def test_fail_update_post_serializer_spot_content_too_long(self) -> None:
        """spot content 3000자 초과 시 실패 테스트"""
        serializer = PostUpdateSerializer(
            data={
                "spots": [
                    {
                        "order": 1,
                        "content": "a" * 3001,
                        "location": {
                            "place_name": "성산일출봉",
                            "address_name": "제주특별자치도 서귀포시 성산읍 성산리 1",
                            "road_address_name": "제주특별자치도 서귀포시 성산읍 일출로 284-12",
                            "x": "126.942492",
                            "y": "33.458421",
                        },
                    }
                ]
            }
        )
        self.assertFalse(serializer.is_valid())

    def test_fail_update_post_serializer_spot_no_location(self) -> None:
        """spot에 location 누락 시 실패 테스트"""
        serializer = PostUpdateSerializer(
            data={
                "spots": [
                    {
                        "order": 1,
                        "content": "test_content",
                    }
                ]
            }
        )
        self.assertFalse(serializer.is_valid())

    def test_fail_update_post_serializer_spot_no_order(self) -> None:
        """spot에 order 누락 시 실패 테스트"""
        serializer = PostUpdateSerializer(
            data={
                "spots": [
                    {
                        "content": "test_content",
                        "location": {
                            "place_name": "성산일출봉",
                            "address_name": "제주특별자치도 서귀포시 성산읍 성산리 1",
                            "road_address_name": "제주특별자치도 서귀포시 성산읍 일출로 284-12",
                            "x": "126.942492",
                            "y": "33.458421",
                        },
                    }
                ]
            }
        )
        self.assertFalse(serializer.is_valid())
