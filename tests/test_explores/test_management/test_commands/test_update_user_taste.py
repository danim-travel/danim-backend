from datetime import timedelta
from unittest import mock

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase
from django.utils import timezone

from apps.posts.models import PostClick, PostEmbedding, PostLike
from apps.users.models import UserTaste
from tests.test_explores.utils import _make_user, make_post, make_rec, user_and_post

# 커맨드 모듈 안에서 이름 탐지 함수를 patch 해야 한다.
# (from ... import get_latest_codebook_version 로 가져왔으므로
#  원본 모듈이 아니라 '커맨드 모듈에 바인딩된 이름'을 patch 한다.)
CMD_PATH = "apps.explores.management.commands.update_user_taste"
VERSION_PATCH = f"{CMD_PATH}.get_latest_codebook_version"


def _set_created(instance, when):
    """auto_now_add 필드(created_at)를 과거로 강제로 민다."""
    type(instance).objects.filter(pk=instance.pk).update(created_at=when)
    instance.refresh_from_db()


def _interact(model, user, post, *, days_ago=0):
    """
    유저 상호작용(PostLike/Comment/PostClick/BookMark) 1건 생성.

    프로젝트 모델 필드가 다르면 여기 한 곳만 고치면 된다.
    가정: 각 모델이 user, post FK 를 가지며 created_at 은 auto_now_add.
    """
    obj = model.objects.create(user=user, post=post)
    if days_ago:
        _set_created(obj, timezone.now() - timedelta(days=days_ago))
    return obj


class GateMissingCodewordTests(TestCase):
    """게이트: 미배정 글이 있으면 스킵 / 24h grace."""

    def _run(self, version="v1"):
        with mock.patch(VERSION_PATCH, return_value=version):
            call_command("update_user_taste")

    def test_no_codebook_raises(self):
        """버전 자동탐지가 None 이면 CommandError."""
        with mock.patch(VERSION_PATCH, return_value=None):
            with self.assertRaises(CommandError):
                call_command("update_user_taste")

    def test_old_unassigned_post_skips_update(self):
        """24h 넘은 글이 해당 버전 codeword 미배정이면 → 전체 스킵, taste 미생성."""
        user, post = user_and_post()
        # 임베딩만 있고 codeword 없음 + 임베딩을 25시간 전으로
        emb, _ = PostEmbedding.objects.get_or_create(post=post)
        _set_created(emb, timezone.now() - timedelta(hours=25))
        _interact(PostLike, user, post)

        self._run(version="v1")

        # 게이트에 걸려 스킵 → UserTaste 가 만들어지지 않아야 함
        self.assertFalse(UserTaste.objects.filter(user=user).exists())

    def test_recent_unassigned_post_within_grace_does_not_skip(self):
        """24h 이내 미배정 글은 grace 로 봐주고 → 갱신 진행."""
        user, post = user_and_post()
        # 이 글은 임베딩만, codeword 없음. 단 '방금' 생성(grace 안)
        emb, _ = PostEmbedding.objects.get_or_create(post=post)
        _set_created(emb, timezone.now() - timedelta(hours=1))

        # 갱신이 실제로 일어나려면 codeword 달린 글이 하나는 있어야 한다
        # (build_codeword_counts 가 None 이 아니게)
        good = make_post(user, days_ago=1)
        make_rec(good, [{"codeword": 10, "weight": 1.0}], version="v1")
        _interact(PostLike, user, good)

        self._run(version="v1")

        # grace 로 스킵 안 됐고, codeword 있는 글 기준으로 taste 생성됨
        taste = UserTaste.objects.get(user=user)
        self.assertEqual(taste.codebook_version, "v1")
        self.assertIn("10", taste.codeword_counts)

    def test_version_mismatch_counts_as_missing(self):
        """v1 codeword 는 있지만 v2 로 계산하려 하면 → 미배정으로 잡혀 스킵."""
        user, post = user_and_post()
        post_old = make_post(user, days_ago=2)
        make_rec(post_old, [{"codeword": 10, "weight": 1.0}], version="v1")
        # 임베딩 created_at 을 grace 밖으로
        _set_created(post_old.rec, timezone.now() - timedelta(hours=30))
        _interact(PostLike, user, post_old)

        self._run(version="v2")  # v2 기준 → v1 행은 미배정 취급

        self.assertFalse(UserTaste.objects.filter(user=user).exists())


class ActiveUserSelectionTests(TestCase):
    """활동 유저 선별 + --all 동작."""

    def _good_post_for(self, user, *, codeword=10):
        post = make_post(user, days_ago=1)
        make_rec(post, [{"codeword": codeword, "weight": 1.0}], version="v1")
        return post

    def test_only_active_users_updated_by_default(self):
        """기본 실행: 7일 이내 상호작용 유저만 갱신."""
        active = _make_user()
        inactive = _make_user()

        post_a = self._good_post_for(active)
        post_i = self._good_post_for(inactive)

        _interact(PostLike, active, post_a, days_ago=1)  # 최근 활동
        _interact(PostLike, inactive, post_i, days_ago=30)  # 7일 밖

        with mock.patch(VERSION_PATCH, return_value="v1"):
            call_command("update_user_taste")

        self.assertTrue(UserTaste.objects.filter(user=active).exists())
        self.assertFalse(UserTaste.objects.filter(user=inactive).exists())

    def test_all_flag_includes_inactive(self):
        """--all: 비활동 유저도 갱신."""
        inactive, _ = user_and_post()
        post_i = self._good_post_for(inactive)
        _interact(PostLike, inactive, post_i, days_ago=30)

        with mock.patch(VERSION_PATCH, return_value="v1"):
            call_command("update_user_taste", "--all")

        self.assertTrue(UserTaste.objects.filter(user=inactive).exists())

    def test_active_user_without_codewords_not_saved(self):
        """활동은 했지만 codeword 달린 글이 없으면(build 결과 None) 저장 안 됨."""
        user, post = user_and_post()
        # codeword 없는 글에만 상호작용 → build_codeword_counts 가 None
        emb, _ = PostEmbedding.objects.get_or_create(post=post)
        _set_created(
            emb, timezone.now() - timedelta(hours=1)
        )  # grace 안이라 게이트는 통과
        _interact(PostLike, user, post, days_ago=1)

        with mock.patch(VERSION_PATCH, return_value="v1"):
            call_command("update_user_taste")

        self.assertFalse(UserTaste.objects.filter(user=user).exists())


class VersionResolutionTests(TestCase):
    """버전 자동탐지 vs --version override."""

    def _setup_user_with_versioned_post(self, version):
        user, post = user_and_post()
        p = make_post(user, days_ago=1)
        make_rec(p, [{"codeword": 10, "weight": 1.0}], version=version)
        _interact(PostLike, user, p, days_ago=1)
        return user

    def test_version_option_overrides_autodetect(self):
        """--version 이 자동탐지보다 우선."""
        user = self._setup_user_with_versioned_post("v2")

        # 자동탐지는 v1 을 주지만, --version v2 로 덮어쓴다
        with mock.patch(VERSION_PATCH, return_value="v1"):
            call_command("update_user_taste", "--codebook-version", "v2")

        taste = UserTaste.objects.get(user=user)
        self.assertEqual(taste.codebook_version, "v2")

    def test_autodetect_used_when_no_option(self):
        """옵션 없으면 자동탐지 버전 사용."""
        user = self._setup_user_with_versioned_post("v1")

        with mock.patch(VERSION_PATCH, return_value="v1"):
            call_command("update_user_taste")

        taste = UserTaste.objects.get(user=user)
        self.assertEqual(taste.codebook_version, "v1")


class CleanupTests(TestCase):
    """정리: 오래된 PostClick / stale UserTaste 삭제."""

    def test_old_clicks_deleted_after_calculation(self):
        """7일 넘은 클릭 삭제, 7일 이내는 보존."""
        user, post = user_and_post()
        good = make_post(user, days_ago=1)
        make_rec(good, [{"codeword": 10, "weight": 1.0}], version="v1")
        _interact(PostLike, user, good, days_ago=1)

        recent_click = _interact(PostClick, user, good, days_ago=3)
        old_click = _interact(PostClick, user, good, days_ago=10)

        with mock.patch(VERSION_PATCH, return_value="v1"):
            call_command("update_user_taste")

        self.assertTrue(PostClick.objects.filter(pk=recent_click.pk).exists())
        self.assertFalse(PostClick.objects.filter(pk=old_click.pk).exists())

    def test_stale_taste_deleted(self):
        """180일 넘게 갱신 안 된 UserTaste 삭제."""
        user, post = user_and_post()
        good = make_post(user, days_ago=1)
        make_rec(good, [{"codeword": 10, "weight": 1.0}], version="v1")
        _interact(PostLike, user, good, days_ago=1)

        stale = UserTaste.objects.create(
            user=user, codeword_counts={"1": 1.0}, codebook_version="v1", alpha=0.5
        )
        # updated_at 은 auto_now → 강제로 과거로
        UserTaste.objects.filter(pk=stale.pk).update(
            updated_at=timezone.now() - timedelta(days=200)
        )

        with mock.patch(VERSION_PATCH, return_value="v1"):
            call_command("update_user_taste")

        # 갱신되면 updated_at 이 now 로 바뀌어 삭제 대상에서 빠진다.
        # 이 유저는 활동 유저이므로 재계산 → 보존되는 게 정상.
        self.assertTrue(UserTaste.objects.filter(user=user).exists())

    def test_truly_stale_taste_of_inactive_user_deleted(self):
        """비활동 + 180일 초과 → 삭제."""
        # 활동 유저가 아니면 재계산 대상이 아니라 updated_at 이 안 바뀜
        user = self._make_inactive_user_with_stale_taste()

        with mock.patch(VERSION_PATCH, return_value="v1"):
            call_command("update_user_taste")

        self.assertFalse(UserTaste.objects.filter(user=user).exists())

    def _make_inactive_user_with_stale_taste(self):
        user, _ = user_and_post()
        taste = UserTaste.objects.create(
            user=user, codeword_counts={"1": 1.0}, codebook_version="v1", alpha=0.5
        )
        UserTaste.objects.filter(pk=taste.pk).update(
            updated_at=timezone.now() - timedelta(days=200)
        )
        return user
