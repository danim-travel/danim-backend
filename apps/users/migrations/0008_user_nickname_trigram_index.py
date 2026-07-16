"""유저 검색(nickname__icontains)용 trigram GIN 인덱스.

중위 LIKE('%x%')는 nickname의 unique B-tree 인덱스를 못 타 유저 테이블
풀스캔이었다. pg_trgm 확장은 posts 0008(TrigramExtension)에서 이미 활성화됨.
"""

from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.operations import AddIndexConcurrently
from django.db import migrations


class Migration(migrations.Migration):

    # CREATE INDEX CONCURRENTLY 는 트랜잭션 밖에서만 실행 가능
    atomic = False

    dependencies = [
        ("users", "0007_user_unread_noti_count_non_negative"),
        # pg_trgm 확장(TrigramExtension) 활성화 이후에 실행돼야 한다
        ("posts", "0008_enable_vector_extension"),
    ]

    operations = [
        AddIndexConcurrently(
            model_name="user",
            index=GinIndex(
                fields=["nickname"],
                opclasses=["gin_trgm_ops"],
                name="ix_users_nickname_trgm",
            ),
        ),
    ]
