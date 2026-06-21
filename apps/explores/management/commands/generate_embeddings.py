"""
파이프라인:
    generate_embeddings  *
    -> bake_codebook
    -> load_codewords
    -> update_user_taste


PostRec에 센터링된 임베딩을 생성하는 커맨드.
새 게시글이 들어와도 처음 커맨드를 가동할 때 만든 평균치를 그대로 재사용하다가,
커맨드에 --all을 붙이면 모든 게시글을 재계산.

산출물: embedding_mean.npy
    임베딩들의 무게중심을 저장한 파일. 이후 저장될 글들의 임베딩을 센터링하기 위해 필요.
"""

import os

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.core.utils.paths import get_artifact_dir
from apps.posts.models import Post, PostEmbedding

EXPECTED_DIM = 1024
EMBEDDING_MODEL = "BAAI/bge-m3"


MEAN_PATH = get_artifact_dir() / "embedding_mean.npy"

BATCH_SIZE = 100


def build_text(post) -> str:
    """
    한 게시글을 임베딩에 넣을 텍스트로 만든다(제목 + 본문 + 스팟 설명).
    테스트 때는 도시 관련 벡터가 과대평가 됐어서 여기에 도시명 제거 로직이 들어있었음.
    """
    parts = [post.title, post.description]
    for spot in post.spots.all():
        if spot.content:
            parts.append(spot.content)
    return "\n".join(p for p in parts if p and p.strip())


class Command(BaseCommand):
    help = "PostRec.embedding(센터링된 임베딩)을 생성합니다."

    def add_arguments(self, parser):
        parser.add_argument("--model", default=EMBEDDING_MODEL)
        parser.add_argument(
            "--all",
            action="store_true",
            help="전부 다시 인코딩하고 전역 평균도 새로 계산",
        )

    def handle(self, *args, **options):
        import numpy as np

        qs = Post.objects.all()
        remake_mean = options["all"] or not MEAN_PATH.exists()

        if not remake_mean:
            qs = qs.filter(rec__embedding__isnull=True)
        posts = list(qs.prefetch_related("spots", "spots__location"))

        if not posts:
            self.stdout.write("인코딩할 글이 없습니다.")
            return

        # 무거운 라이브러리라 레이지 임포트
        from sentence_transformers import SentenceTransformer

        model = SentenceTransformer(options["model"])
        get_dim = (
            getattr(model, "get_embedding_dimension", None)
            or getattr(model, "get_sentence_embedding_dimension", None)
            or getattr(model, "get_word_embedding_dimension", None)
        )
        # dim이 None, 즉 차원을 알아내지 못했다면 에러 내지 않고 일단 계산을 돌려봄
        dim = get_dim() if get_dim else None
        if dim is not None and dim != EXPECTED_DIM:
            raise CommandError(f"모델 차원 {dim}개. {EXPECTED_DIM}가 아닙니다.")

        # 배포용은 raw_embedding 컬럼 삭제. DB에 저장하지 않고 메모리에서 작업
        self.stdout.write(f"인코딩: {len(posts)}건")
        # raw: dict(post, vector)
        raw = {}
        for i in range(0, len(posts), BATCH_SIZE):
            batch = posts[i : i + BATCH_SIZE]
            vecs = model.encode([build_text(p) for p in batch], normalize_embeddings=True)
            for p, v in zip(batch, vecs):
                raw[p] = np.asarray(v, dtype="float64")

        # --all이거나 mean 파일이 없으면 raw로 평균을 새로 만들고 저장
        # 평균 파일이 있고 부분 run이면 기존 평균 재사용
        if remake_mean:
            mean = np.stack(list(raw.values())).mean(axis=0)
            np.save(MEAN_PATH, mean)
            self.stdout.write(f"전역 평균 생성: {MEAN_PATH}")
        else:
            mean = np.load(MEAN_PATH)
            self.stdout.write(f"전역 평균 재사용: {MEAN_PATH}")

        # 센터링, 노멀라이즈 후 PostRec.embedding에 저장
        items = list(raw.items())
        with transaction.atomic():
            for i in range(0, len(items), BATCH_SIZE):
                batch = items[i : i + BATCH_SIZE]
                centered = np.stack([v for _, v in batch]) - mean
                norms = np.linalg.norm(centered, axis=1, keepdims=True)
                norms[norms == 0] = 1.0  # 평균과 정확히 같은 벡터 보호(0 division 방지)
                centered /= norms

                # 호환 안정성을 위해 tolist로 numpy 배열을 파이썬 리스트로 변환
                recs = []
                for (p, _), c in zip(batch, centered):
                    recs.append(PostEmbedding(post=p, embedding=c.tolist()))

                PostEmbedding.objects.bulk_create(
                    recs,
                    update_conflicts=True,
                    unique_fields=["post"],
                    update_fields=["embedding"],
                )

        self.stdout.write(self.style.SUCCESS(f"{len(raw)}건 완료"))
        self.stdout.flush()
        os._exit(0)
