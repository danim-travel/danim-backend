from django.test import TestCase

from apps.posts.serializers.serializer import PostCreateSerializer


class PostCreateSerializerTest(TestCase):

    def test_create_post_serializer(self) -> None:
        """게시글 생성 serializer 성공 테스트"""
        serializer = PostCreateSerializer(
            data={
                "title": "test_title",
                "description": "test_description",
                "thumbnail": "prod/posts/thumbnail/uuid.jpg",
                "spots": [
                    {
                        "order": 1,
                        "content": "test_content",
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
                                "key": "prod/posts/uuid.jpg",
                            }
                        ],
                    }
                ],
            }
        )
        self.assertTrue(serializer.is_valid())

    def test_fail_create_post_serializer_no_title(self) -> None:
        """title 누락 시 실패 테스트"""
        serializer = PostCreateSerializer(
            data={
                "description": "test_description",
                "spots": [],
            }
        )
        self.assertFalse(serializer.is_valid())

    def test_fail_create_post_serializer_title_too_long(self) -> None:
        """title 100자 초과 시 실패 테스트"""
        serializer = PostCreateSerializer(
            data={
                "title": "a" * 101,
                "spots": [],
            }
        )
        self.assertFalse(serializer.is_valid())

    def test_fail_create_post_serializer_no_location(self) -> None:
        """spot에 location 누락 시 실패 테스트"""
        serializer = PostCreateSerializer(
            data={
                "title": "test_title",
                "spots": [
                    {
                        "order": 1,
                        "content": "test_content",
                    }
                ],
            }
        )
        self.assertFalse(serializer.is_valid())

    def test_fail_create_post_serializer_no_order(self) -> None:
        """spot에 order 누락 시 실패 테스트"""
        serializer = PostCreateSerializer(
            data={
                "title": "test_title",
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
                ],
            }
        )
        self.assertFalse(serializer.is_valid())
