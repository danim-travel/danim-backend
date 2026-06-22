import shutil
import tempfile
from io import StringIO
from pathlib import Path
from unittest import mock

import numpy as np
from django.core.management import call_command
from django.test import TestCase

# EDIT: 실제 커맨드 모듈 경로에 맞춰 수정
from apps.explores.management.commands import bake_codebook as cmd
from apps.posts.models import PostEmbedding
from tests.test_explores.utils import make_post, make_shared_user

COMMAND = "bake_codebook"
DIM = 1024


def seed_embeddings(user, n, *, seed=0):
    """글 n건 + 단위벡터 임베딩을 심는다. r.embedding은 이미 노멀라이즈됐다는 전제."""
    rng = np.random.default_rng(seed)
    embs = []
    for _ in range(n):
        post = make_post(user)
        v = rng.standard_normal(DIM)
        v = v / np.linalg.norm(v)
        embs.append(PostEmbedding.objects.create(post=post, embedding=v.tolist()))
    return embs


class TestBakeCodebook(TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.codebook_path = Path(self.tmp) / "codebook.npy"
        patcher = mock.patch.object(cmd, "CODEBOOK_PATH", self.codebook_path)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.addCleanup(lambda: shutil.rmtree(self.tmp, ignore_errors=True))

    def _run(self, *args):
        call_command(COMMAND, *args, stdout=StringIO())

    def test_no_embeddings_returns_early(self):
        make_shared_user()  # 글 0건 → 임베딩 0건
        self._run()
        self.assertFalse(self.codebook_path.exists())  # 파일조차 안 만듦

    def test_k_equals_len_when_fewer_than_K(self):
        # 글 5건 < K → min(K, 5) = 5. 코드북 행 수가 글 수와 같아야 함
        seed_embeddings(make_shared_user(), 5)
        self._run()
        cb = np.load(self.codebook_path)
        self.assertEqual(cb.shape, (5, DIM))

    def test_k_caps_at_K_when_more_than_K(self):
        # K를 3으로 줄여 "글 수 > K" 분기를 싸게 검증. min(3, 10) = 3
        seed_embeddings(make_shared_user(), 10)
        with mock.patch.object(cmd, "K", 3):
            self._run()
        cb = np.load(self.codebook_path)
        self.assertEqual(cb.shape, (3, DIM))

    def test_centroids_are_normalized(self):
        seed_embeddings(make_shared_user(), 10)
        with mock.patch.object(cmd, "K", 4):
            self._run()
        cb = np.load(self.codebook_path)
        norms = np.linalg.norm(cb, axis=1)
        self.assertTrue(np.allclose(norms, 1.0, atol=1e-6))  # 각 코드워드는 단위벡터

    def test_reproducible_with_same_input_and_seed(self):
        seed_embeddings(make_shared_user(), 10)
        with mock.patch.object(cmd, "K", 4):
            self._run()
            cb1 = np.load(self.codebook_path)
            self._run()  # 같은 입력 + 같은 SEED로 다시
            cb2 = np.load(self.codebook_path)
        self.assertTrue(np.array_equal(cb1, cb2))  # 동일 코드북
