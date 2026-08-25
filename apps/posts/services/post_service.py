from typing import Any

from django.conf import settings
from django.db import transaction
from django.db.models import BooleanField, Exists, F, OuterRef, Value

from apps.core.exceptions.exception import NotFoundException
from apps.follows.models import Follows
from apps.posts.models import (
    BookMark,
    Location,
    Post,
    PostClick,
    PostLike,
    PostSpot,
    PostSpotImage,
)
from apps.users.models import User


class PostService:
    def create_post(self, data: dict[str, Any], user: User) -> Post:
        """게시글 생성 서비스 로직"""
        with transaction.atomic():
            post = Post.objects.create(
                user=user,
                title=data["title"],
                description=data.get("description", ""),
                thumbnail=data.get("thumbnail", ""),
                thumbnail_width=data.get("thumbnail_width"),
                thumbnail_height=data.get("thumbnail_height"),
            )

            spots_data = data.get("spots", [])
            for spot_data in spots_data:
                self._create_spot_with_location_and_images(post, spot_data)
            if spots_data:
                Post.objects.filter(id=post.id).update(spot_count=len(spots_data))

        return post

    def get_list(self, user: User) -> Any:
        """
        팔로잉한 유저의 게시글만 목록으로 조회하는 서비스 로직

        annotate로 좋아요, 북마크 여부도 필드에 포함시켜서 반환.
        """
        following_users = Follows.objects.filter(follower=user).values_list(
            "following", flat=True
        )
        queryset = Post.objects.filter(user__in=following_users)
        queryset = queryset.select_related("user").prefetch_related("spots__location")
        queryset = queryset.annotate(
            is_liked=Exists(PostLike.objects.filter(user=user, post_id=OuterRef("pk"))),
            is_bookmarked=Exists(
                BookMark.objects.filter(user=user, post_id=OuterRef("pk"))
            ),
        )
        return queryset

    def get_post_detail(self, post_id: str, user: User) -> Any:
        """
        게시글 상세 조회 서비스 로직
        """
        if not Post.objects.filter(id=post_id).exists():
            raise NotFoundException("게시글을 찾을 수 없습니다.")

        with transaction.atomic():
            queryset = Post.objects.filter(id=post_id)
            queryset = queryset.select_related("user").prefetch_related(
                "spots__location", "spots__images"
            )
            queryset = queryset.annotate(
                is_liked=(
                    Exists(PostLike.objects.filter(user=user, post_id=OuterRef("pk")))
                    if user.is_authenticated
                    else Value(False, output_field=BooleanField())
                ),
                is_bookmarked=(
                    Exists(BookMark.objects.filter(user=user, post_id=OuterRef("pk")))
                    if user.is_authenticated
                    else Value(False, output_field=BooleanField())
                ),
                is_owner=(
                    Exists(Post.objects.filter(id=post_id, user=user))
                    if user.is_authenticated
                    else Value(False, output_field=BooleanField())
                ),
            )
            post = queryset.first()

            if user.is_authenticated:
                PostClick.objects.create(user=user, post_id=post_id)
            Post.objects.filter(id=post_id).update(view_count=F("view_count") + 1)

        return post

    def update_post(self, post_id: str, data: dict[str, Any], user: User) -> None:
        with transaction.atomic():
            try:
                post = Post.objects.select_for_update().get(id=post_id, user=user)
            except Post.DoesNotExist:
                raise NotFoundException("게시글을 찾을 수 없습니다.")

            if "title" in data:
                post.title = data["title"]
            if "description" in data:
                post.description = data["description"]
            if "thumbnail" in data:
                post.thumbnail = data["thumbnail"]
            if "thumbnail_width" in data:
                post.thumbnail_width = data["thumbnail_width"]
            if "thumbnail_height" in data:
                post.thumbnail_height = data["thumbnail_height"]
            post.save()

            if "spots" in data:
                post.spots.all().delete()
                Location.objects.filter(post_spots__isnull=True).delete()
                spots_data = data["spots"]
                for spot_data in spots_data:
                    self._create_spot_with_location_and_images(post, spot_data)
                Post.objects.filter(id=post.id).update(spot_count=len(spots_data))

    def delete_post(self, post_id: str, user: User) -> None:
        with transaction.atomic():
            try:
                post = Post.objects.select_for_update().get(id=post_id, user=user)
            except Post.DoesNotExist:
                raise NotFoundException("게시글을 찾을 수 없습니다.")
            post.delete()
            Location.objects.filter(post_spots__isnull=True).delete()

    def get_share_url(self, post_id: str) -> str:
        """게시글 공유 서비스 로직"""
        try:
            Post.objects.get(id=post_id)
        except Post.DoesNotExist:
            raise NotFoundException("게시글을 찾을 수 없습니다.")

        return f"{settings.FRONTEND_URL}/posts/{post_id}"

    def _create_spot_with_location_and_images(self, post: Post, spot_data: dict) -> None:
        location_data = spot_data["location"]
        location = Location.objects.create(
            address_name=location_data["address_name"],
            road_address_name=location_data["road_address_name"],
            place_name=location_data["place_name"],
            x=location_data["x"],
            y=location_data["y"],
        )
        post_spot = PostSpot.objects.create(
            post=post,
            location=location,
            content=spot_data.get("content", ""),
            order=spot_data["order"],
        )

        images = [
            PostSpotImage(
                post_spot=post_spot,
                img_key=image_data["key"],
                original_img=image_data["original_img"],
                img_order=img_order,
                width=image_data["width"],
                height=image_data["height"],
            )
            for img_order, image_data in enumerate(spot_data.get("images", []), start=1)
        ]
        if images:
            PostSpotImage.objects.bulk_create(images)
