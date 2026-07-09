import math

from django.db.models import F, FloatField, Value
from django.db.models.functions import ASin, Cast, Cos, Power, Radians, Sin, Sqrt

from apps.posts.models import PostSpot

DANIM_RADIUS = 3
R = 6371.0


def _get_range_latitude(lat: float):
    """최대 위도값 ,최소 위도값 구하는 함수"""
    min_lat = lat - (DANIM_RADIUS / 111.0)
    max_lat = lat + (DANIM_RADIUS / 111.0)
    return min_lat, max_lat


def _get_range_longitude(lon: float, lat: float):
    """최대 경도값 ,최소 경도값 구하는 함수"""
    min_lon = lon - (DANIM_RADIUS / (111.0 * math.cos(math.radians(lat))))
    max_lon = lon + (DANIM_RADIUS / (111.0 * math.cos(math.radians(lat))))
    return min_lon, max_lon


def _get_queryset_on_range(
    lat: float, lon: float, min_lat: float, max_lat: float, min_lon: float, max_lon: float
):
    """
    유저의 좌표 기준으로 3km씩 각각의 위도 최댓값과 최솟값을 사용해서 좌표 범위로 1차 필티렁
    이후 haversine으로 실제 거리로 2차 필터링
    이후 사용자와의 거리를 기준으로 정렬하고 top 10만 출력
    """
    queryset = (
        PostSpot.objects.filter(
            location__x__lt=max_lon,
            location__x__gt=min_lon,
            location__y__lt=max_lat,
            location__y__gt=min_lat,
        )
        .select_related("location", "post")
        .annotate(distance=_get_haversine_expression(lat, lon))
        .filter(distance__lte=DANIM_RADIUS)
        .order_by("distance")[:10]
    )

    return queryset


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
    return 6371 * 2 * ASin(Sqrt(a))


def get_near_post_queryset(data: dict):
    lat = data["latitude"]
    lon = data["longitude"]

    min_lat, max_lat = _get_range_latitude(lat)
    min_lon, max_lon = _get_range_longitude(lon, lat)

    queryset = _get_queryset_on_range(lat, lon, min_lat, max_lat, min_lon, max_lon)

    return queryset
