from django.db.models import QuerySet

from apps.posts.models import PostSpot
from apps.posts.near_postspot.services.near_user_service import get_near_post_queryset


def get_spots(data: dict) -> tuple[QuerySet[PostSpot] | None, str]:
    post_id = data["post_id"]
    spots = PostSpot.objects.filter(post_id=post_id).select_related("location").all()
    if not spots:
        return None, post_id
    return spots, post_id


def get_postspot_list(spots: QuerySet[PostSpot] | None, post_id: str) -> dict:
    if spots is None:
        return {"post_id": post_id, "near_spots": []}
    spot_list = []
    for spot in spots:
        n_s = {}
        data = {"latitude": float(spot.location.y), "longitude": float(spot.location.x)}
        near_spot_list = get_near_post_queryset(data, exclude_post_id=post_id)
        n_s["spot_id"] = spot.id
        n_s["top_near"] = near_spot_list
        spot_list.append(n_s)

    result = {
        "post_id": post_id,
        "near_spots": spot_list,
    }

    return result
