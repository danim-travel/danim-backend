import shutil
import tempfile
from io import StringIO
from pathlib import Path
from unittest import mock

import numpy as np
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

# EDIT: 실제 커맨드 모듈 경로에 맞춰 수정
from apps.explores.management.commands import load_codewords as cmd
from apps.posts.models import PostCodeword, PostEmbedding
from tests.test_explores.utils import make_post, make_shared_user

COMMAND = "load_codewords"
DIM = 1024


def basis_codebook(k, dim=DIM):
    """코드워드 i = i번째 기저 벡터(e_i). 단위벡터이므로 그대로 코사인 유사도가 된다."""
    cb = np.zeros((k, dim), dtype="float64")
    for i in range(k):
        cb[i, i] = 1.0
    return cb


def make_emb(user, coeffs, dim=DIM):
    """coeffs = [(인덱스, 값), ...] 로 벡터를 만들어 노멀라이즈 후 임베딩으로 저장.

    기저 코드북과 내적하면 sim_j = (노멀라이즈된) coeffs[j] 가 되어 결과를 손계산할 수 있다.
    """
    v = np.zeros(dim, dtype="float64")
    for idx, val in coeffs:
        v[idx] = val
    v = v / np.linalg.norm(v)
    post = make_post(user)
    return PostEmbedding.objects.create(post=post, embedding=v.tolist())


def assign(emb, version, codewords):
    return PostCodeword.objects.create(
        embedding=emb, codewords=codewords, codebook_version=version
    )


def weights_of(codewords):
    return [c["weight"] for c in codewords]


def codes_of(codewords):
    return [c["codeword"] for c in codewords]


class TestLoadCodewords(TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(lambda: shutil.rmtree(self.tmp, ignore_errors=True))
        self.user = make_shared_user()

    def _use_codebook(self, version, centroids):
        """temp/<version>/codebook.npy 를 만들고 get_latest_codebook_dir 가 그걸 보게 한다."""
        d = Path(self.tmp) / version
        d.mkdir(parents=True, exist_ok=True)
        np.save(d / "codebook.npy", centroids)
        patcher = mock.patch.object(cmd, "get_latest_codebook_dir", return_value=d)
        patcher.start()
        self.addCleanup(patcher.stop)
        return d

    def _run(self, *args):
        call_command(COMMAND, *args, stdout=StringIO())

    # ── 가드 ───────────────────────────────────────────────────────────────
    def test_no_codebook_dir_raises(self):
        with mock.patch.object(cmd, "get_latest_codebook_dir", return_value=None):
            with self.assertRaises(CommandError):
                self._run()

    def test_no_npy_raises(self):
        d = Path(self.tmp) / "v1"
        d.mkdir(parents=True)  # 폴더만 있고 codebook.npy 없음
        with mock.patch.object(cmd, "get_latest_codebook_dir", return_value=d):
            with self.assertRaises(CommandError):
                self._run()

    def test_dim_mismatch_raises(self):
        make_emb(self.user, [(0, 1.0)])  # 1024차원 임베딩
        self._use_codebook("v1", basis_codebook(5, dim=512))  # 512차원 코드북
        with self.assertRaises(CommandError):
            self._run()

    def test_no_embeddings_returns_early(self):
        self._use_codebook("v1", basis_codebook(5))  # 임베딩 0건
        self._run()
        self.assertEqual(PostCodeword.objects.count(), 0)

    # ── 배정 계산 ──────────────────────────────────────────────────────────
    def test_assigns_top3_with_known_weights(self):
        # coeffs 3:2:1 → sim 비율 3:2:1 → 정규화 가중치 0.5 / 0.3333 / 0.1667
        emb = make_emb(self.user, [(0, 3.0), (1, 2.0), (2, 1.0)])
        self._use_codebook("v1", basis_codebook(5))
        self._run()

        pc = PostCodeword.objects.get(embedding=emb)
        self.assertEqual(pc.codebook_version, "v1")
        self.assertEqual(codes_of(pc.codewords), [0, 1, 2])  # 유사도 내림차순
        w = weights_of(pc.codewords)
        self.assertAlmostEqual(w[0], 0.5, places=4)
        self.assertAlmostEqual(w[1], 0.3333, places=4)
        self.assertAlmostEqual(w[2], 0.1667, places=4)
        self.assertAlmostEqual(sum(w), 1.0, places=3)  # 가중치 합 = 1

    def test_each_post_gets_its_own_codewords(self):
        # 순서 매칭이 어긋나면 A가 B의 코드워드를 받게 되는 회귀를 잡는다.
        a = make_emb(self.user, [(0, 3.0), (1, 2.0), (2, 1.0)])  # top → 0
        b = make_emb(self.user, [(4, 3.0), (3, 2.0), (2, 1.0)])  # top → 4
        self._use_codebook("v1", basis_codebook(5))
        self._run()

        pc_a = PostCodeword.objects.get(embedding=a)
        pc_b = PostCodeword.objects.get(embedding=b)
        self.assertEqual(codes_of(pc_a.codewords), [0, 1, 2])
        self.assertEqual(codes_of(pc_b.codewords), [4, 3, 2])

    def test_all_negative_sims_fall_back_to_uniform(self):
        # 모든 코드워드와 음의 유사도 → 클램프 후 합 0 → 균등 가중치
        emb = make_emb(self.user, [(i, -1.0) for i in range(5)])
        self._use_codebook("v1", basis_codebook(5))
        self._run()

        pc = PostCodeword.objects.get(embedding=emb)
        w = weights_of(pc.codewords)
        self.assertEqual(len(w), 3)
        for x in w:
            self.assertAlmostEqual(x, 0.3333, places=4)  # 1/3씩

    # ── 버전 / 대상 선정 ───────────────────────────────────────────────────
    def test_default_skips_already_assigned_latest(self):
        emb = make_emb(self.user, [(0, 1.0)])
        sentinel = [{"codeword": 99, "weight": 1.0}]
        assign(emb, "v1", sentinel)  # 이미 최신(v1) 배정 존재
        self._use_codebook("v1", basis_codebook(5))
        self._run()

        # 새 행이 안 생기고, 기존 행도 안 건드려져야 함
        self.assertEqual(PostCodeword.objects.filter(embedding=emb).count(), 1)
        self.assertEqual(PostCodeword.objects.get(embedding=emb).codewords, sentinel)

    def test_default_reassigns_old_version_only_post(self):
        emb = make_emb(self.user, [(0, 3.0), (1, 2.0), (2, 1.0)])
        old = assign(emb, "v1", [{"codeword": 99, "weight": 1.0}])  # 구버전 배정
        self._use_codebook("v2", basis_codebook(5))  # 최신은 v2
        self._run()

        # v1은 그대로 남고, v2 행이 새로 생겨 공존
        rows = PostCodeword.objects.filter(embedding=emb)
        self.assertEqual(rows.count(), 2)
        v2 = rows.get(codebook_version="v2")
        self.assertEqual(codes_of(v2.codewords), [0, 1, 2])
        old.refresh_from_db()
        self.assertEqual(old.codewords, [{"codeword": 99, "weight": 1.0}])

    def test_all_recomputes_existing_latest(self):
        emb = make_emb(self.user, [(0, 3.0), (1, 2.0), (2, 1.0)])
        assign(emb, "v1", [{"codeword": 99, "weight": 1.0}])  # 최신(v1) 배정 존재
        self._use_codebook("v1", basis_codebook(5))
        self._run("--all")  # 기존 행 삭제 후 재계산

        # 여전히 1건이지만 내용이 실제 계산값으로 갈림(99 사라짐)
        rows = PostCodeword.objects.filter(embedding=emb, codebook_version="v1")
        self.assertEqual(rows.count(), 1)
        self.assertEqual(codes_of(rows.get().codewords), [0, 1, 2])
