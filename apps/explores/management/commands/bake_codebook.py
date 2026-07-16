"""
파이프라인:
    generate_embeddings
    -> bake_codebook  *
    -> load_codewords
    -> update_user_taste


게시글의 임베딩을 재료로 K-means를 10회 돌려 그 중 가장 적합한 코드워드를 생성

산출물:
    codebook.npy: 코드워드의 번호와 벡터(행: 번호, 열: 벡터). 신규글의 클러스터 배정에 쓰임.
"""

import numpy as np
from django.core.management import BaseCommand
from sklearn.cluster import KMeans

from apps.core.utils.paths import get_next_codebook_dir
from apps.posts.models.rec_models import PostEmbedding

K = 80  # 코드워드 개수
TOP_N = 3  # 게시글당 배정할 코드워드 수
SEED = 42  # 고정하면 매번 같은 코드북이 나옴

# 저장 경로. None이면 handle() 실행 시점에 새 버전 디렉토리를 만든다.
# (테스트에서 mock.patch로 주입할 수 있도록 모듈 속성으로 유지)
# 주의: get_next_codebook_dir()를 모듈 레벨에서 호출하면 "임포트만으로"
# 빈 vN+1 디렉토리가 생긴다 — 테스트 실행·`manage.py help`조차 새 버전을 만들고,
# get_latest_codebook_dir()가 그 빈 디렉토리를 최신으로 인식해
# load_codewords/update_user_taste 파이프라인이 통째로 멈춘다.
CODEBOOK_PATH = None


def normalize(np_array):
    norm = np.linalg.norm(np_array, axis=1, keepdims=True)
    norm[norm == 0] = 1.0
    return np_array / norm


class Command(BaseCommand):
    help = "코드워드를 생성하고 게시글을 근접한 3개의 코드워드에 배정합니다."

    def handle(self, *args, **options):

        recs = list(PostEmbedding.objects.filter(embedding__isnull=False))
        if not recs:
            return

        # r.embedding은 이미 노멀라이즈된 벡터
        # emb_np: 2차원 배열. 행=글 번호, 열=글 벡터
        emb_np = np.asarray([r.embedding for r in recs], dtype="float64")

        # K가 np_array 수보다 많으면 에러가 나서 적음
        k = min(K, len(emb_np))

        # 재료가 되는 임베딩이 같으면 항상 같은 코드북을 도출하도록 시드를 정함.
        k_means = KMeans(n_clusters=k, n_init=10, random_state=SEED)
        k_means.fit(emb_np)
        # centroids: 2차원 배열 행=클러스터 번호, 열=클러스터 벡터
        centroids = normalize(k_means.cluster_centers_.astype("float64"))

        # 새 버전 디렉토리는 저장 직전에만 생성한다 (임포트 부작용 방지).
        codebook_path = CODEBOOK_PATH or (get_next_codebook_dir() / "codebook.npy")
        np.save(codebook_path, centroids)
