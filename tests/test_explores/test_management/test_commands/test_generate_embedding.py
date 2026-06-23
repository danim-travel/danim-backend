import shutil
import sys
import tempfile
import types
from io import StringIO
from pathlib import Path
from unittest import mock

import numpy as np
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

# EDIT: 실제 커맨드 모듈 경로/파일명에 맞춰 두 줄 수정
from apps.explores.management.commands import generate_embeddings as cmd
from apps.posts.models import Post, PostEmbedding
from tests.test_explores.utils import make_post, make_shared_user

COMMAND = "generate_embeddings"

DIM = 1024


class FakeModel:
    """SentenceTransformer 대역. encode 는 i번째 글에 e_i(원핫)를 돌려준다."""

    def __init__(self, dim=DIM):
        self._dim = dim
        self.encoded = []  # 본 텍스트 누적(몇 건 인코딩됐는지 검증용)

    def get_sentence_embedding_dimension(self):
        return self._dim

    def encode(self, texts, normalize_embeddings=False):
        texts = list(texts)
        self.encoded.extend(texts)
        arr = np.zeros((len(texts), self._dim), dtype="float32")
        for i in range(len(texts)):
            arr[i, i % self._dim] = 1.0
        return arr


# ── build_text: 순수 함수 (목 불필요) ──────────────────────────────────────
class TestBuildText(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = make_shared_user()

    def test_joins_title_and_description(self):
        p = make_post(self.user)  # title="t", description="d"
        self.assertEqual(cmd.build_text(p), "t\nd")

    def test_none_title_kept_description(self):
        p = make_post(self.user)
        p.title = None  # in-memory 변경(DB NOT NULL 제약 회피)
        self.assertEqual(cmd.build_text(p), "d")

    def test_blank_and_whitespace_dropped(self):
        p = make_post(self.user)
        p.title = None
        p.description = "   "
        self.assertEqual(cmd.build_text(p), "")  # p.strip() 필터로 전부 제외


# ── handle: 분기 로직 ──────────────────────────────────────────────────────
class TestGenerateEmbeddings(TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.mean_path = Path(self.tmp) / "embedding_mean.npy"
        patcher = mock.patch.object(cmd, "MEAN_PATH", self.mean_path)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.addCleanup(lambda: shutil.rmtree(self.tmp, ignore_errors=True))

    def _run(self, model, *args):
        """SentenceTransformer 를 가짜로 끼우고, os._exit 를 무력화한 뒤 실행."""
        fake_mod = types.ModuleType("sentence_transformers")
        fake_mod.SentenceTransformer = lambda *a, **k: model
        with (
            mock.patch.dict(sys.modules, {"sentence_transformers": fake_mod}),
            mock.patch("os._exit"),
        ):
            call_command(COMMAND, *args, stdout=StringIO())
        return model

    def test_dim_mismatch_raises(self):
        make_post(make_shared_user())
        with self.assertRaises(CommandError):
            self._run(FakeModel(dim=512))

    def test_no_posts_returns_early(self):
        make_shared_user()  # 글 0건
        model = self._run(FakeModel())
        self.assertEqual(model.encoded, [])  # 인코딩 자체를 안 함
        self.assertFalse(self.mean_path.exists())  # 평균도 안 만듦
        self.assertEqual(PostEmbedding.objects.count(), 0)

    def test_first_run_creates_mean_and_centers_single_to_zero(self):
        p = make_post(make_shared_user())
        self._run(FakeModel())
        self.assertTrue(self.mean_path.exists())
        self.assertEqual(np.load(self.mean_path).shape, (DIM,))
        # 글 1건이면 mean=그 벡터 → centered 0 → (0division 가드로) 0벡터 저장
        vec = np.asarray(PostEmbedding.objects.get(post=p).embedding, dtype=float)
        self.assertTrue(np.allclose(vec, 0.0, atol=1e-5))

    def test_two_posts_centered_and_normalized(self):
        u = make_shared_user()
        make_post(u)
        make_post(u)
        self._run(FakeModel())
        vecs = [np.asarray(e.embedding, dtype=float) for e in PostEmbedding.objects.all()]
        self.assertEqual(len(vecs), 2)
        for v in vecs:
            self.assertAlmostEqual(np.linalg.norm(v), 1.0, places=4)  # 단위벡터
        self.assertTrue(np.allclose(vecs[0], -vecs[1], atol=1e-3))  # 대칭(±)

    def test_partial_run_reuses_mean_and_skips_existing(self):
        u = make_shared_user()
        make_post(u)
        make_post(u)
        self._run(FakeModel())  # 1차: 전체
        mean_before = np.load(self.mean_path)

        new_post = make_post(u)  # 임베딩 아직 없음
        model2 = self._run(FakeModel())  # 2차: --all 없이(부분)

        self.assertEqual(len(model2.encoded), 1)  # 새 글만 인코딩
        self.assertTrue(
            np.array_equal(mean_before, np.load(self.mean_path))
        )  # 평균 그대로
        self.assertEqual(PostEmbedding.objects.count(), 3)
        self.assertTrue(PostEmbedding.objects.filter(post=new_post).exists())

    def test_all_flag_reencodes_everything(self):
        u = make_shared_user()
        make_post(u)
        make_post(u)
        self._run(FakeModel())  # 1차
        model2 = self._run(FakeModel(), "--all")  # 이미 임베딩 있어도
        self.assertEqual(len(model2.encoded), 2)  # 전부 다시 인코딩
