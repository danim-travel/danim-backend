"""
파이프라인:
    generate_embeddings
    -> bake_codebook
    -> load_codewords
    -> update_user_taste  *

UserTaste 일일 갱신 + 오래된 PostClick, UserTaste 정리.
최신 코드북 버전을 자동 탐지한 뒤, 임베딩이 있는 글이 전부 그 버전 codeword에 배정됐는지 검증한다.
하나라도 미배정이면 이번 실행을 통째로 스킵하고 기존 taste 를 보존함.
스킵 조건은 작성된지 24시간 이후 글에 대해서만 적용된다.
즉 24시간 이내 작성된 글의 코드워드가 최신이 아니더라도 스킵되지 않음.

--version 옵션으로 유저 취향을 계산할 코드워드 버전을 지정할 수 있다.
--all 옵션으로 모든 유저의 취향을 계산한다. 기본값은 7일 이내 활동 유저만 가져와서 계산.
"""

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from apps.comments.models import Comment
from apps.core.utils.paths import get_latest_codebook_version
from apps.explores.services.taste import (
    build_codeword_counts_bulk,
    collect_taste_events_bulk,
    personalization_alpha,
)
from apps.posts.models import BookMark, PostClick, PostEmbedding, PostLike
from apps.users.models import UserTaste

User = get_user_model()

USER_ACTIVE_DAYS = 7
CLICK_RETENTION_DAYS = 7
TASTE_TTL_DAYS = 180
USER_CHUNK_SIZE = 2000


def _chunked(seq, size=USER_CHUNK_SIZE):
    """--all 처럼 대상 유저가 많을 때 메모리/IN절 크기를 고정하기 위한 배치 분할."""
    for i in range(0, len(seq), size):
        yield seq[i : i + size]


def _active_user_ids(cutoff):
    user_ids = set()
    for model in (PostLike, Comment, PostClick, BookMark):
        ids = model.objects.filter(created_at__gte=cutoff).values_list(
            "user_id", flat=True
        )
        user_ids.update(ids)
    return user_ids


def _missing_codeword_count(version, grace_hours=24):
    """
    임베딩이 있는 게시글이 모두 해당 버전 코드워드에 배정돼 있는지 확인.
    배정 안 된 글이 1건이라도 있으면 0보다 큰 값을 반환 -> taste 갱신 스킵.
    단, 작성된 지 24h 이내인 글은 아직 처리 중인 정상 상태로 보고 검사에서 제외한다.
    """
    cutoff = timezone.now() - timedelta(hours=grace_hours)
    return (
        PostEmbedding.objects.filter(embedding__isnull=False, created_at__lt=cutoff)
        .exclude(clusters__codebook_version=version)
        .count()
    )


class Command(BaseCommand):
    help = "유저 취향 갱신 + 오래된 클릭/취향 정리"

    def add_arguments(self, parser):
        parser.add_argument(
            "--codebook-version",
            dest="version",
            help="취향을 계산할 코드북 버전 지정",
        )
        parser.add_argument(
            "--all",
            action="store_true",
            help="비활동 유저 포함 전체 유저 재계산",
        )

    def handle(self, *args, **options):
        version = options["version"] or get_latest_codebook_version()
        if version is None:
            raise CommandError("코드북이 없음")

        missing = _missing_codeword_count(version)
        if missing > 0:
            # 이번 실행 스킵, 기존 taste 는 그대로 보존
            self.stdout.write(
                self.style.WARNING(f"{version} codeword 없는 글 {missing}건. 갱신 스킵")
            )
            return

        now = timezone.now()

        if options["all"]:
            users = User.objects.all()
        else:
            cutoff = now - timedelta(days=USER_ACTIVE_DAYS)
            users = User.objects.filter(id__in=_active_user_ids(cutoff))

        user_ids = list(users.values_list("id", flat=True))

        updated = 0
        for chunk in _chunked(user_ids):
            events_by_user, last_active_by_user = collect_taste_events_bulk(
                chunk, now=now
            )
            counts_by_user = build_codeword_counts_bulk(
                events_by_user, version=version, now=now
            )

            rows = [
                UserTaste(
                    user_id=user_id,
                    codeword_counts=counts["counts"],
                    codebook_version=counts["version"],
                    alpha=personalization_alpha(
                        None,  # events 를 넘기면 user 는 내부에서 쓰이지 않음
                        events=events_by_user[user_id],
                        last_active=last_active_by_user.get(user_id),
                        now=now,
                    ),
                )
                for user_id, counts in counts_by_user.items()
            ]

            UserTaste.objects.bulk_create(
                rows,
                update_conflicts=True,
                # updated_at(auto_now)은 update_fields에 명시해야 conflict 시에도 갱신됨.
                # 빠지면 활성 유저의 updated_at이 최초 생성 시각에 고정돼
                # 아래 TASTE_TTL_DAYS 정리 로직이 활성 유저를 오삭제하게 됨.
                update_fields=[
                    "codeword_counts",
                    "codebook_version",
                    "alpha",
                    "updated_at",
                ],
                unique_fields=["user"],
                batch_size=1000,
            )
            updated += len(rows)

        # taste 계산이 클릭을 쓰니까 반드시 계산 이후에 삭제
        click_cutoff = now - timedelta(days=CLICK_RETENTION_DAYS)
        deleted, _ = PostClick.objects.filter(created_at__lt=click_cutoff).delete()

        taste_cutoff = now - timedelta(days=TASTE_TTL_DAYS)
        taste_deleted, _ = UserTaste.objects.filter(updated_at__lt=taste_cutoff).delete()

        self.stdout.write(
            self.style.SUCCESS(
                f"[{version}] 취향 {updated}명 갱신, "
                f"오래된 클릭 {deleted}건, stale 유저 취향 {taste_deleted}건 삭제"
            )
        )
