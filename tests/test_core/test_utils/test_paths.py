"""codebook 버전 디렉토리 헬퍼 검증.

과거 bake_codebook이 모듈 임포트만으로 빈 vN+1 디렉토리를 만들었고,
get_latest_codebook_dir가 그 빈 디렉토리를 최신으로 인식해
load_codewords/update_user_taste 일일 파이프라인이 통째로 멈췄다.
여기서는 "codebook.npy가 있는 버전만 최신 후보"라는 계약과
버전 이름 파싱의 견고함(v1_backup 무시)을 고정한다.
"""

import shutil
import tempfile
from pathlib import Path

from django.test import TestCase, override_settings

from apps.core.utils.paths import (
    get_latest_codebook_dir,
    get_latest_codebook_version,
    get_next_codebook_dir,
)


class CodebookPathsTest(TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: shutil.rmtree(self.tmp, ignore_errors=True))
        self._override = override_settings(BASE_DIR=self.tmp)
        self._override.enable()
        self.addCleanup(self._override.disable)
        self.codebook_root = self.tmp / "artifacts" / "codebook"

    def _make_version(self, name: str, with_npy: bool = True) -> Path:
        d = self.codebook_root / name
        d.mkdir(parents=True, exist_ok=True)
        if with_npy:
            (d / "codebook.npy").touch()
        return d

    def test_latest_skips_empty_version_dirs(self):
        """빈 버전 디렉토리(중단된 베이크)는 최신 후보가 아니다."""
        v1 = self._make_version("v1", with_npy=True)
        self._make_version("v2", with_npy=False)  # 빈 디렉토리
        self.assertEqual(get_latest_codebook_dir(), v1)
        self.assertEqual(get_latest_codebook_version(), "v1")

    def test_latest_returns_none_without_usable_version(self):
        """codebook.npy가 있는 버전이 하나도 없으면 None."""
        self._make_version("v1", with_npy=False)
        self.assertIsNone(get_latest_codebook_dir())
        self.assertIsNone(get_latest_codebook_version())

    def test_non_numeric_version_dirs_are_ignored(self):
        """v1_backup 같은 수동 디렉토리가 있어도 죽지 않고 무시한다."""
        v1 = self._make_version("v1", with_npy=True)
        self._make_version("v1_backup", with_npy=True)
        self.assertEqual(get_latest_codebook_dir(), v1)  # 과거엔 ValueError
        self.assertEqual(get_next_codebook_dir(), self.codebook_root / "v2")

    def test_next_counts_empty_dirs_for_numbering(self):
        """다음 버전 번호는 빈 디렉토리도 포함해 계산 — 기존 버전을 덮어쓰지 않는다."""
        self._make_version("v1", with_npy=True)
        self._make_version("v2", with_npy=False)
        self.assertEqual(get_next_codebook_dir(), self.codebook_root / "v3")
