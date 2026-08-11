"""`scripts/check_hook_pins.py` 회귀 테스트.

이 스크립트는 다른 검사를 지키는 게이트라 조용히 망가지면 알아채기 어렵다. 특히
"검사를 통과시키는 잘못된 방법"(고정값 삭제, 훅 저장소 추가, 공백 넣기)이 실제로
막히는지 확인한다.
"""

import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]

_spec = importlib.util.spec_from_file_location(
    "check_hook_pins", ROOT / "scripts" / "check_hook_pins.py"
)
assert _spec is not None and _spec.loader is not None
check_hook_pins = importlib.util.module_from_spec(_spec)
sys.modules["check_hook_pins"] = check_hook_pins
_spec.loader.exec_module(check_hook_pins)


LOCK = """
[[package]]
name = "black"
version = "26.5.1"

[[package]]
name = "isort"
version = "8.0.1"

[[package]]
name = "mypy"
version = "1.13.0"

[[package]]
name = "pre-commit"
version = "4.6.0"

[[package]]
name = "django"
version = "6.0.5"

[[package]]
name = "Pillow"
version = "11.0.0"

[[package]]
name = "torch"
version = "2.12.1"

[[package]]
name = "torch"
version = "2.12.1+cpu"
"""

MAKEFILE = (
    "hooks:\n\tuv tool install pre-commit==4.6.0\n\tuv tool run pre-commit install\n"
)

CONFIG = """repos:
  - repo: https://github.com/psf/black
    rev: 26.5.1
    hooks:
      - id: black

  - repo: https://github.com/PyCQA/isort
    rev: 8.0.1
    hooks:
      - id: isort

  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v6.0.0
    hooks:
      - id: trailing-whitespace

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.13.0
    hooks:
      - id: mypy
        additional_dependencies:
          # 주석은 건너뛴다
          - django==6.0.5
          - httpx
"""


def run(config=CONFIG, lock=LOCK, makefile=MAKEFILE, max_unpinned=1):
    """샘플 설정의 미고정은 httpx 1개뿐이므로 래칫 기준도 1로 두고 검사한다."""
    return check_hook_pins.check(config, lock, makefile, max_unpinned)


def test_기준_설정은_통과한다():
    errors, unpinned, checked = run()
    assert errors == []
    assert unpinned == ["httpx"]
    assert checked == 5  # 저장소 3 + Makefile 1 + 고정 의존성 1


def test_rev_가_어긋나면_실패한다():
    errors, _, _ = run(config=CONFIG.replace("rev: v1.13.0", "rev: v1.11.0"))
    assert any("rev 불일치: mypy" in e for e in errors)


def test_고정값이_어긋나면_실패한다():
    errors, _, _ = run(config=CONFIG.replace("django==6.0.5", "django==5.0.0"))
    assert any("핀 불일치: django" in e for e in errors)


def test_uv_lock_에_없는_패키지는_실패한다():
    errors, _, _ = run(config=CONFIG.replace("django==6.0.5", "nonexistent-pkg==1.0.0"))
    assert any("없습니다" in e for e in errors)


def test_공백을_넣어도_고정으로_인식한다():
    """`django == 6.0.5` 를 '미고정' 으로 흘려보내면 검사에서 빠져버린다."""
    errors, unpinned, _ = run(config=CONFIG.replace("django==6.0.5", "django == 6.0.5"))
    assert unpinned == ["httpx"]
    errors, _, _ = run(config=CONFIG.replace("django==6.0.5", "django == 5.0.0"))
    assert any("핀 불일치: django" in e for e in errors)


def test_고정값을_지워_우회하면_실패한다():
    """래칫 — 값을 고치는 대신 == 를 지우는 우회로를 막는다."""
    errors, unpinned, _ = run(config=CONFIG.replace("django==6.0.5", "django"))
    assert len(unpinned) == 2
    assert any("늘었습니다" in e for e in errors)


def test_새로_고정하면_래칫_기준을_낮추라고_실패한다():
    """기준선이 느슨한 채로 남으면 다음 우회를 못 막는다."""
    errors, unpinned, _ = run(config=CONFIG.replace("- httpx", "- Pillow==11.0.0"))
    assert unpinned == []
    assert any("MAX_UNPINNED 를 0 로 낮추세요" in e for e in errors)


def test_인라인_표기는_통과시키지_않는다():
    """`additional_dependencies: [a, b]` 로 바꾸면 고정값이 통째로 검사에서 빠진다."""
    inline = CONFIG.replace(
        "        additional_dependencies:\n"
        "          # 주석은 건너뛴다\n"
        "          - django==6.0.5\n"
        "          - httpx\n",
        "        additional_dependencies: [django==5.0.0, httpx]\n",
    )
    errors, _, _ = run(config=inline)
    assert errors  # 조용히 [OK] 가 나오면 안 된다


def test_매핑없는_저장소를_추가하면_실패한다():
    """새 훅이 조용히 검사 밖에 놓이지 않도록."""
    added = CONFIG + "\n  - repo: https://github.com/example/unknown\n    rev: v1.0.0\n"
    errors, _, _ = run(config=added)
    assert any("매핑 없는 훅 저장소" in e for e in errors)


def test_uv_lock_에_중복된_패키지는_임의값과_비교하지_않는다():
    """torch 처럼 이름이 두 번 오르는 패키지는 대조 대상이 되면 실패해야 한다."""
    errors, _, _ = run(config=CONFIG.replace("django==6.0.5", "torch==2.12.1"))
    assert any("여러 버전으로 있습니다" in e for e in errors)


def test_Makefile_의_pre_commit_버전도_대조한다():
    errors, _, _ = run(
        makefile=MAKEFILE.replace("pre-commit==4.6.0", "pre-commit==4.0.0")
    )
    assert any("핀 불일치: pre-commit" in e for e in errors)


def test_Makefile_에서_설치줄이_사라지면_실패한다():
    errors, _, _ = run(makefile="hooks:\n\tuv tool run pre-commit install\n")
    assert any("찾지 못했습니다" in e for e in errors)


def test_파싱_결과가_비면_통과시키지_않는다():
    errors, _, _ = run(config="repos:\n")
    assert any("파싱 결과가 비었습니다" in e for e in errors)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("django==6.0.5", "django==6.0.5"),
        ("django == 6.0.5  # 주석", "django==6.0.5"),
        ('"django==6.0.5"', "django==6.0.5"),
        ("django-storages[s3]==1.14.6", "django-storages[s3]==1.14.6"),
    ],
)
def test_의존성_표기_정리(raw, expected):
    assert check_hook_pins.clean_dep(raw) == expected


def test_실제_저장소_파일이_통과한다():
    """테스트용 샘플이 아니라 지금 저장소에 있는 실제 파일로 한 번 더 확인한다."""
    errors, unpinned, _ = check_hook_pins.check(
        (ROOT / ".pre-commit-config.yaml").read_text(encoding="utf-8"),
        (ROOT / "uv.lock").read_text(encoding="utf-8"),
        (ROOT / "Makefile").read_text(encoding="utf-8"),
    )
    assert errors == []
    assert len(unpinned) == check_hook_pins.MAX_UNPINNED
