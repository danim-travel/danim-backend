from collections import defaultdict
from datetime import timedelta

from django.utils import timezone

from apps.comments.models import Comment
from apps.posts.models import BookMark, PostClick, PostCodeword, PostLike

TASTE_HORIZON_DAYS = 365

ALPHA_FULL = 100

TASTE_WEIGHTS = {
    "like": 0.8,
    "comment": 0.8,
    "click": 0.2,
    "bookmark": 1.2,
}

_TASTE_SOURCES = (
    (PostLike, "like"),
    (Comment, "comment"),
    (PostClick, "click"),
    (BookMark, "bookmark"),
)


def collect_taste_events(user, now=None):
    """
    유저의 상호작용을 (post_id, weight_key, created_at) 리스트와
    가장 최근 활동일로 한 번에 모아 반환.
    TASTE_HORIZON_DAYS 보다 오래된 이벤트는 제외한다.
    personalization_alpha / build_codeword_counts 가 이 결과를 공유해서
    같은 유저에 대해 4개 테이블을 두 번 조회하지 않도록 한다.
    """
    now = now or timezone.now()
    cutoff = now - timedelta(days=TASTE_HORIZON_DAYS)

    events = []
    last_active = None
    for model, weight_key in _TASTE_SOURCES:
        rows = model.objects.filter(user=user, created_at__gte=cutoff).values(
            "post_id", "created_at"
        )
        for row in rows:
            created_at = row["created_at"]
            events.append((row["post_id"], weight_key, created_at))
            if last_active is None or created_at > last_active:
                last_active = created_at

    return events, last_active


def collect_taste_events_bulk(user_ids, now=None):
    """
    여러 유저의 상호작용을 한 번에 모아 user_id 별로 묶어서 반환.
    (events_by_user, last_active_by_user) — 둘 다 user_id 를 키로 하는 dict.
    collect_taste_events 를 유저 수만큼 반복 호출하면 모델당 1쿼리 * 유저 수가
    나가지만, 이 함수는 모델당 1쿼리(총 4쿼리)로 대상 유저 수와 무관하게 고정된다.
    """
    now = now or timezone.now()
    cutoff = now - timedelta(days=TASTE_HORIZON_DAYS)

    events_by_user = defaultdict(list)
    last_active_by_user = {}
    for model, weight_key in _TASTE_SOURCES:
        rows = model.objects.filter(user_id__in=user_ids, created_at__gte=cutoff).values(
            "user_id", "post_id", "created_at"
        )
        for row in rows:
            uid = row["user_id"]
            created_at = row["created_at"]
            events_by_user[uid].append((row["post_id"], weight_key, created_at))
            if uid not in last_active_by_user or created_at > last_active_by_user[uid]:
                last_active_by_user[uid] = created_at

    return events_by_user, last_active_by_user


def personalization_alpha(user, *, events=None, last_active=None, now=None):
    now = now or timezone.now()
    if events is None:
        events, last_active = collect_taste_events(user, now=now)

    if last_active is None:
        return 0.0

    strength = sum(
        TASTE_WEIGHTS[weight_key]
        * _sigmoid_decay((now - created_at).days, center=90, scale=3)
        for _, weight_key, created_at in events
    )
    alpha = min(1.0, strength / ALPHA_FULL)

    idle_days = (now - last_active).days
    return alpha * _sigmoid_decay(idle_days, center=7, scale=5)


def _sigmoid_decay(age_days, center=7, scale=5):
    return 1.0 / (1.0 + (age_days / center) ** scale)


def _last_active_at(user):
    """유저의 가장 최근 활동일이 언제인지 확인하는 함수"""
    _, last_active = collect_taste_events(user)
    return last_active


def build_codeword_counts(user, version="v1", *, events=None, now=None):
    """
    유저의 상호작용을 코드워드 카운트(희소 맵)로 누적해서 반환.

        {"counts": {"20": 1.83, "10": 0.95, ...}, "version": "v1"}

    누적값 = TASTE_WEIGHTS * 시간감쇠(_sigmoid_decay) * 게시글 codeword 가중치
    결과가 어느 코드북 버전 기준인지 함께 반환한다. 저장 측에서 이 version 을
    UserTaste.codebook_version 에 함께 보관해야, 채점 시 글 버전과 대조해
    버전이 어긋날 때 개인화를 스킵할 수 있다.
    상호작용이 하나도 없으면 None (콜드 스타터).
    """
    now = now or timezone.now()
    if events is None:
        events, _ = collect_taste_events(user, now=now)

    if not events:
        return None

    post_ids = {e[0] for e in events}
    codewords_by_post = _load_codewords(post_ids, version)
    counts = _accumulate_codeword_counts(events, codewords_by_post, now)

    if not counts:
        return None

    return {
        "counts": {k: round(v, 6) for k, v in counts.items()},
        "version": version,
    }


def build_codeword_counts_bulk(events_by_user, version="v1", now=None):
    """
    collect_taste_events_bulk 의 결과(events_by_user)를 받아
    user_id 별 codeword 누적 결과를 한 번에 계산해서 반환.
        {user_id: {"counts": {...}, "version": "v1"}, ...}
    build_codeword_counts 를 유저마다 호출하면 PostCodeword 조회가 유저 수만큼
    나가지만, 이 함수는 전체 유저의 post_id 를 모아 1쿼리로 한 번만 로드한다.
    counts 가 비게 되는(콜드/미배정) 유저는 결과 dict 에 아예 포함되지 않는다.
    """
    now = now or timezone.now()

    all_post_ids = {
        post_id for events in events_by_user.values() for post_id, _, _ in events
    }
    if not all_post_ids:
        return {}

    codewords_by_post = _load_codewords(all_post_ids, version)

    result = {}
    for user_id, events in events_by_user.items():
        counts = _accumulate_codeword_counts(events, codewords_by_post, now)
        if counts:
            result[user_id] = {
                "counts": {k: round(v, 6) for k, v in counts.items()},
                "version": version,
            }
    return result


def _load_codewords(post_ids, version):
    """post_id 집합에 대응하는 codeword 목록을 1쿼리로 로드."""
    return {
        str(row["embedding__post_id"]): row["codewords"]
        for row in PostCodeword.objects.filter(
            embedding__post_id__in=post_ids, codebook_version=version
        ).values("embedding__post_id", "codewords")
    }


def _accumulate_codeword_counts(events, codewords_by_post, now):
    """이벤트 목록 하나를 codeword별 누적값(defaultdict)으로 변환."""
    counts = defaultdict(float)
    for post_id, weight_key, created_at in events:
        cws = codewords_by_post.get(str(post_id))
        # codewords 아직 없는 글은 스킵
        if not cws:
            continue
        age_days = (now - created_at).days
        w = TASTE_WEIGHTS[weight_key] * _sigmoid_decay(age_days, center=60, scale=2)
        for cw in cws:
            counts[str(cw["codeword"])] += w * cw["weight"]
    return counts
