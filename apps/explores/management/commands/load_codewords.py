"""
파이프라인:
    generate_embeddings
    -> bake_codebook
    -> load_codewords  *
    -> update_user_taste


bake_codebook이 구운 codebook.npy를 읽어, 각 글 임베딩을 가장 가까운
TOP_N개의 코드워드에 배정하고 PostCodeword 테이블에 적재한다.

- 코드북 벡터(무거움)는 npy에 그대로 두고, DB엔 (코드워드 번호 + 가중치)만 저장.
- 코드워드 번호 = codebook.npy의 행 인덱스 = sims의 argsort 인덱스.
- 대상: embedding이 있고, 아직 최신 버전으로 배정되지 않은 PostEmbedding.
    신규글이거나 구버전으로만 배정된 글이 모두 여기에 걸린다.
    --all 옵션이 있으면 임베딩이 있는 모든 글을 최신버전으로 재배정.
"""

import numpy as np
from django.core.management import BaseCommand
from django.core.management.base import CommandError
from django.db import transaction
from django.db.models import Exists, OuterRef

from apps.core.utils.paths import get_latest_codebook_dir
from apps.posts.models import PostCodeword, PostEmbedding

TOP_N = 3  # 게시글당 배정할 코드워드 수
BATCH = 500  # bulk_create 묶음 크기


class Command(BaseCommand):
    help = (
        "최신 코드북으로 게시글을 TOP_N개의 코드워드에 배정해 PostCodeword에 적재합니다."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--all",
            action="store_true",
            help="최신 버전에 한해 전부 재배정(기존 행 삭제 후 재생성)",
        )

    def handle(self, *args, **options):
        codebook_dir = get_latest_codebook_dir()
        if codebook_dir is None:
            raise CommandError(
                "코드북을 찾을 수 없습니다. bake_codebook을 먼저 실행하세요."
            )

        codebook_path = codebook_dir / "codebook.npy"
        if not codebook_path.exists():
            raise CommandError(f"codebook.npy가 없습니다: {codebook_path}")

        version = codebook_dir.name  # 폴더명이 곧 버전 문자열 (예: "v1")

        # centroids: 넘파이 2차원 배열. 행=코드워드 번호, 열=코드워드 벡터.
        centroids = np.load(codebook_path).astype("float64")

        # 대상 선정: embedding이 있고, 최신 버전 PostCodeword가 없는 것.
        assigned_latest = PostCodeword.objects.filter(
            embedding=OuterRef("pk"), codebook_version=version
        )
        qs = PostEmbedding.objects.filter(embedding__isnull=False)
        if not options["all"]:
            qs = qs.annotate(has_latest=Exists(assigned_latest)).filter(has_latest=False)

        # recs 순서와 emb_np 행 순서가 어긋나면 A글에 B글 코드워드가 박히므로,
        # 리스트로 한 번 고정하고 그 순서대로 행렬을 쌓는다.
        recs = list(qs)
        if not recs:
            self.stdout.write(f"배정할 임베딩이 없습니다. (version={version})")
            return

        # emb_np: 2차원 배열. 행=글, 열=글 벡터
        emb_np = np.asarray([r.embedding for r in recs], dtype="float64")

        # 행렬곱의 가불가를 확인
        if emb_np.shape[1] != centroids.shape[1]:
            raise CommandError(
                f"차원 불일치: 임베딩 {emb_np.shape[1]} vs 코드북 {centroids.shape[1]}"
            )

        # 행렬곱(@)을 위해 centroids를 전치.
        # sims_array: 2차원 배열. 행=글 번호, 열=클러스터 번호
        # sims_array[i] = i번째 글과 각 코드워드 간의 코사인 유사도.
        sims_array = emb_np @ centroids.T

        objs = []
        for i, emb in enumerate(recs):
            sims = sims_array[i]
            # top_nums: top-N 유사도에 해당하는 코드워드 번호(=행 인덱스)를 내림차순으로.
            top_nums = np.argsort(sims)[-TOP_N:][::-1]
            # weights: 해당 코드워드들의 코사인 유사도. 음수는 0으로 클램프.
            weights = sims[top_nums].copy()
            weights[weights < 0] = 0.0
            summed = weights.sum()
            # 전부 음수라 합이 0이면 균등 가중치로 폴백.
            weights = (
                (weights / summed)
                if summed > 0
                else np.ones(len(top_nums)) / len(top_nums)
            )
            codewords = [
                {"codeword": int(n), "weight": round(float(w), 4)}
                for n, w in zip(top_nums, weights)
            ]
            objs.append(
                PostCodeword(
                    embedding=emb,
                    codewords=codewords,
                    codebook_version=version,
                )
            )

        with transaction.atomic():
            if options["all"]:
                # 재배정: 이 버전의 기존 행을 지우고 새로 만든다.
                # all 옵션이 없으면 delete가 실질적으로 삭제하는 행은 없음.
                PostCodeword.objects.filter(
                    codebook_version=version, embedding__in=recs
                ).delete()
            # 대상 선정에서 이미 최신 버전 행을 제외했으므로 충돌은 거의 없지만,
            # 동시 실행 등에 대비해 unique 충돌은 무시한다.
            PostCodeword.objects.bulk_create(
                objs, ignore_conflicts=True, batch_size=BATCH
            )

        self.stdout.write(f"[완료] PostCodeword {len(objs)}건 적재 (version={version})")
