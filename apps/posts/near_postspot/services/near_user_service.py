import math

from django.db.models import F, FloatField, Q, Value
from django.db.models.functions import ASin, Cast, Cos, Power, Radians, Sin, Sqrt

from apps.posts.models import PostSpot

DANIM_RADIUS = 3
R = 6371.0
KM_PER_DEGREE_LAT = 111.0


def _normalize_longitude(longitude: float) -> float:
    if longitude > 180:
        longitude -= 360
    elif longitude < -180:
        longitude += 360
    return longitude


def _get_range_latitude(lat: float):
    """최대 위도값 ,최소 위도값 구하는 함수"""
    min_lat = lat - (DANIM_RADIUS / KM_PER_DEGREE_LAT)
    max_lat = lat + (DANIM_RADIUS / KM_PER_DEGREE_LAT)
    return min_lat, max_lat


def _get_range_longitude(lon: float, lat: float):
    """최대 경도값 ,최소 경도값 구하는 함수"""
    delta = min(DANIM_RADIUS / (KM_PER_DEGREE_LAT * math.cos(math.radians(lat))), 180)
    min_lon = _normalize_longitude(lon - delta)
    max_lon = _normalize_longitude(lon + delta)
    return min_lon, max_lon


def _get_queryset_on_range(
    lat: float,
    lon: float,
    min_lat: float,
    max_lat: float,
    min_lon: float,
    max_lon: float,
    exclude_post_id: str | None = None,
):
    """
    유저의 좌표 기준으로 3km씩 각각의 위도 최댓값과 최솟값을 사용해서 좌표 범위로 1차 필티렁
    이후 haversine으로 실제 거리로 2차 필터링
    이후 사용자와의 거리를 기준으로 정렬하고 top 10만 출력

    exclude_post_id가 주어지면 해당 게시글의 스팟을 top 10을 자르기 전에 제외한다.
    게시글 주변 조회는 자기 좌표를 기준으로 검색하므로 제외하지 않으면 자기 스팟이
    거리 0으로 항상 상위를 차지해 다른 게시글 자리를 잠식한다.
    """
    if min_lon > max_lon:
        queryset = PostSpot.objects.filter(
            Q(location__x__lte=max_lon) | Q(location__x__gte=min_lon),
            location__y__lte=max_lat,
            location__y__gte=min_lat,
        )
    else:
        queryset = PostSpot.objects.filter(
            location__x__lte=max_lon,
            location__x__gte=min_lon,
            location__y__lte=max_lat,
            location__y__gte=min_lat,
        )

    if exclude_post_id is not None:
        queryset = queryset.exclude(post_id=exclude_post_id)

    return (
        queryset.select_related("location", "post")
        .annotate(distance=_get_haversine_expression(lat, lon))
        .filter(distance__lte=DANIM_RADIUS)
        .order_by("distance")[:10]
    )


def _get_haversine_expression(lat, lon):
    """
    두 좌표(도 단위) 사이의 표면 거리(km)를 Haversine 공식으로 구하는 함수를 Django ORM을 사용해서 Python 객체로 SQL문 생성하는 함수
    """
    y = Cast(F("location__y"), FloatField())
    x = Cast(F("location__x"), FloatField())

    d_phi = Radians(Value(lat) - y)
    d_lambda = Radians(Value(lon) - x)

    phi1 = Radians(Value(lat))
    phi2 = Radians(y)

    a = Power(Sin(d_phi / 2), 2) + Cos(phi1) * Cos(phi2) * Power(Sin(d_lambda / 2), 2)
    return R * 2 * ASin(Sqrt(a))


def get_near_post_queryset(data: dict, exclude_post_id: str | None = None):
    lat = data["latitude"]
    lon = data["longitude"]

    min_lat, max_lat = _get_range_latitude(lat)
    min_lon, max_lon = _get_range_longitude(lon, lat)

    queryset = _get_queryset_on_range(
        lat, lon, min_lat, max_lat, min_lon, max_lon, exclude_post_id
    )

    return queryset
