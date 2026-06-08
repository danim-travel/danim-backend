from apps.posts.serializers import (
    ImageSerializer,
    LocationSerializer,
    PostCreateRequestSerializer,
    SpotSerializer,
)
from tests.test_posts.core import PostBaseTest


class TestPostCreateSerializer(PostBaseTest):

    def setUp(self):
        super().setUp()
        self.data_over_title = {
            "title": "test_title" * 100,
            "description": "test_content",
            "thumbnail": "test_thumbnail",
            "spots": [self.data_for_spot_1, self.data_for_spot_2],
        }
        self.data_miss_field = {
            "title": "test_title",
            "thumbnail": "test_thumbnail",
            "spots": [self.data_for_spot_1, self.data_for_spot_2],
        }
        self.data_fail_spot_str_order = {
            "order": "test_order",
            "content": "test_content",
            "location": self.data_for_location_1,
            "images": [self.data_for_image_1, self.data_for_image_2],
        }
        self.data_fail_spot_order = {
            "order": 0,
            "content": "test_content",
            "location": self.data_for_location_1,
            "images": [self.data_for_image_1, self.data_for_image_2],
        }
        self.data_for_spot_miss_field = {
            "content": "test_content",
            "location": self.data_for_location_1,
            "images": [self.data_for_image_1, self.data_for_image_2],
        }
        self.data_fail_loc_over_str = {
            "address_name": "test_address_name" * 100,
            "road_address_name": "test_road_address_name",
            "place_name": "test_place_name",
            "x": "125.05758310323952",
            "y": "31.49813536728827",
        }
        self.data_fail_loc_miss_field = {
            "road_address_name": "test_road_address_name",
            "place_name": "test_place_name",
            "x": "125.05758310323952",
            "y": "31.49813536728827",
        }
        self.data_fail_loc_over_x_y = {
            "address_name": "test_address_name",
            "road_address_name": "test_road_address_name",
            "place_name": "test_place_name",
            "x": "125.05758410323952",
            "y": "31.49813577777777777777776728827",
        }
        self.data_fail_img_miss_field = {
            "original_img": "test_original_img",
        }

    def test_post_create_serializer(self):
        """PostCreateRequestSerializer 성공 테스트"""
        serializer = PostCreateRequestSerializer(data=self.data_for_create_view)
        self.assertTrue(serializer.is_valid())

    def test_post_fail_over_title(self):
        """PostCreateRequestSerializer title필드 글자수 제한 테스트"""
        serializer = PostCreateRequestSerializer(data=self.data_over_title)
        self.assertFalse(serializer.is_valid())

    def test_post_fail_miss_fields(self):
        """PostCreateReqeustSerializer 필수 필드 누락 테스트"""
        serializer = PostCreateRequestSerializer(data=self.data_miss_field)
        self.assertFalse(serializer.is_valid())

    def test_spot_fail_invalid_order(self):
        """SpotSerializer order필드 형변환 실패 테스트"""
        serializer = SpotSerializer(data=self.data_fail_spot_str_order)
        self.assertFalse(serializer.is_valid())

    def test_spot_fail_min_order(self):
        """SpotSerializer order 필드 최소값 테스트"""
        serializer = SpotSerializer(data=self.data_fail_spot_order)
        self.assertFalse(serializer.is_valid())

    def test_spot_fail_miss_field(self):
        """SpotSerializer 필수 필드 누락 테스트"""
        serializer = SpotSerializer(data=self.data_for_spot_miss_field)
        self.assertFalse(serializer.is_valid())

    def test_location_fail_over_address(self):
        """LocationSerializer 문자열 최대자리수 제한 테스트"""
        serializer = LocationSerializer(data=self.data_fail_loc_over_str)
        self.assertFalse(serializer.is_valid())

    def test_location_fail_miss_field(self):
        """LocationSerializer 필수 필드 누락 테스트"""
        serializer = LocationSerializer(data=self.data_fail_loc_miss_field)
        self.assertFalse(serializer.is_valid())

    def test_location_fail_over_x_y(self):
        """LocationSerializer 좌표 최대 자리수 초과 테스트"""
        serializer = LocationSerializer(data=self.data_fail_loc_over_x_y)
        self.assertFalse(serializer.is_valid())

    def test_image_fail_miss_field(self):
        """ImageSerializer 필수 필드 누락 테스트"""
        serializer = ImageSerializer(data=self.data_fail_img_miss_field)
        self.assertFalse(serializer.is_valid())
