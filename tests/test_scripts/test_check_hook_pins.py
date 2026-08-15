"""`scripts/check_hook_pins.py` 회귀 테스트.

이 스크립트는 다른 검사를 지키는 게이트라 조용히 망가지면 알아채기 어렵다. 특히
"검사를 통과시키는 잘못된 방법"이 실제로 막히는지를 중심으로 본다 — 값 오염뿐 아니라
줄 삭제·주석 처리·맞바꾸기·인라인 표기·extra 제거까지.
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
name = "django-stubs"
version = "6.0.4"

[[package]]
name = "Pillow"
version = "11.0.0"

[[package]]
name = "torch"
version = "2.12.1"

[[package]]
name = "torch"
version = "2.12.1+cpu"

[[package]]
name = "danim-backend"
version = "0.1.0"
source = { virtual = "." }

[package.metadata]
requires-dist = []

[package.metadata.requires-dev]
dev = [
    { name = "django-stubs", extras = ["compatible-mypy"], specifier = ">=6.0.4" },
]
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
          - django-stubs[compatible-mypy]==6.0.4
          - httpx
"""

REQUIRED = {"django", "django-stubs"}
ALLOWED = {"httpx"}


def run(config=CONFIG, lock=LOCK, makefile=MAKEFILE, required=None, allowed=None):
    return check_hook_pins.check(
        config,
        lock,
        makefile,
        REQUIRED if required is None else required,
        ALLOWED if allowed is None else allowed,
    )


def test_기준_설정은_통과한다():
    errors, checked = run()
    assert errors == []
    assert checked == 6  # 저장소 3 + Makefile 1 + 고정 의존성 2


# ── 값 오염 ────────────────────────────────────────────────────────────────────


def test_rev_가_어긋나면_실패한다():
    errors, _ = run(config=CONFIG.replace("rev: v1.13.0", "rev: v1.11.0"))
    assert any("rev 불일치: mypy" in e for e in errors)


def test_고정값이_어긋나면_실패한다():
    errors, _ = run(config=CONFIG.replace("django==6.0.5", "django==5.0.0"))
    assert any("핀 불일치: django" in e for e in errors)


def test_uv_lock_에_없는_패키지는_실패한다():
    errors, _ = run(
        config=CONFIG.replace("django==6.0.5", "nonexistent-pkg==1.0.0"),
        required={"nonexistent-pkg", "django-stubs"},
    )
    assert any("없습니다" in e for e in errors)


def test_uv_lock_에_중복된_패키지는_임의값과_비교하지_않는다():
    """torch 처럼 이름이 두 번 오르는 패키지는 대조 대상이 되면 실패해야 한다."""
    errors, _ = run(
        config=CONFIG.replace("django==6.0.5", "torch==2.12.1"),
        required={"torch", "django-stubs"},
    )
    assert any("여러 버전으로 있습니다" in e for e in errors)


# ── 우회 시도: 값을 고치는 대신 구조를 건드리는 경우 ────────────────────────────


def test_고정값의_등호를_지우면_실패한다():
    errors, _ = run(config=CONFIG.replace("django==6.0.5", "django"))
    assert any("고정이 풀린 패키지" in e and "django" in e for e in errors)


def test_줄을_통째로_지우면_실패한다():
    """개수 래칫이 못 잡던 자리 — 지워진 줄은 미고정 목록에도 안 들어간다."""
    errors, checked = run(config=CONFIG.replace("          - django==6.0.5\n", ""))
    assert any("사라진 고정 대상" in e and "django" in e for e in errors)
    assert checked == 5  # 6 -> 5 로 줄어드는 것도 함께 확인


def test_줄을_주석_처리해도_실패한다():
    errors, _ = run(
        config=CONFIG.replace("          - django==6.0.5", "          # - django==6.0.5")
    )
    assert any("사라진 고정 대상" in e and "django" in e for e in errors)


def test_고정_대상과_미고정_항목을_맞바꿔도_실패한다():
    """개수는 그대로라 개수 래칫은 통과시키던 자리."""
    swapped = CONFIG.replace("django==6.0.5", "django").replace(
        "- httpx", "- httpx==0.28.1"
    )
    errors, _ = run(config=swapped)
    assert any("고정이 풀린 패키지" in e and "django" in e for e in errors)


def test_미고정_항목이_사라져도_실패한다():
    errors, _ = run(config=CONFIG.replace("          - httpx\n", ""))
    assert any("사라진 항목" in e and "httpx" in e for e in errors)


def test_목록에_없는_의존성을_추가하면_실패한다():
    """등록 없이 슬쩍 늘어나는 것도 막는다."""
    errors, _ = run(config=CONFIG.replace("- httpx", "- httpx\n          - celery"))
    assert any("목록에 없는 의존성" in e and "celery" in e for e in errors)


def test_extra_를_떼면_실패한다():
    """[compatible-mypy] 가 빠지면 mypy 버전 제약이 통째로 사라진다(원 장애의 원인)."""
    errors, _ = run(
        config=CONFIG.replace(
            "django-stubs[compatible-mypy]==6.0.4", "django-stubs==6.0.4"
        )
    )
    assert any("extra 누락" in e and "django-stubs" in e for e in errors)


def test_프로젝트를_못_찾으면_extra_대조를_포기하지_않는다():
    """이름 대신 source 로 찾으므로, 그마저 없으면 조용히 통과시키면 안 된다."""
    errors, _ = run(lock=LOCK.replace('source = { virtual = "." }', ""))
    assert any("프로젝트 자신을 찾지 못해" in e for e in errors)


def test_인라인_표기는_통과시키지_않는다():
    """`additional_dependencies: [a, b]` 로 바꾸면 고정값이 통째로 검사에서 빠진다."""
    inline = CONFIG.replace(
        "        additional_dependencies:\n"
        "          # 주석은 건너뛴다\n"
        "          - django==6.0.5\n"
        "          - django-stubs[compatible-mypy]==6.0.4\n"
        "          - httpx\n",
        "        additional_dependencies: [django==5.0.0, httpx]\n",
    )
    errors, _ = run(config=inline)
    assert errors  # 조용히 [OK] 가 나오면 안 된다


def test_매핑없는_저장소를_추가하면_실패한다():
    """새 훅이 조용히 검사 밖에 놓이지 않도록."""
    added = CONFIG + "\n  - repo: https://github.com/example/unknown\n    rev: v1.0.0\n"
    errors, _ = run(config=added)
    assert any("매핑 없는 훅 저장소" in e for e in errors)


def test_파싱_결과가_비면_통과시키지_않는다():
    errors, _ = run(config="repos:\n")
    assert any("파싱 결과가 비었습니다" in e for e in errors)


def test_이해할_수_없는_표기는_통과시키지_않는다():
    """>= 같은 범위 표기를 '미고정' 으로 조용히 넘기면 의도가 흐려진다."""
    errors, _ = run(config=CONFIG.replace("django==6.0.5", "django>=6.0.5"))
    assert any("이해할 수 없는" in e for e in errors)


# ── 파싱 세부 ──────────────────────────────────────────────────────────────────


def test_공백을_넣어도_고정으로_인식한다():
    """`django == 6.0.5` 를 '미고정' 으로 흘려보내면 검사에서 빠져버린다."""
    errors, _ = run(config=CONFIG.replace("django==6.0.5", "django == 6.0.5"))
    assert errors == []
    errors, _ = run(config=CONFIG.replace("django==6.0.5", "django == 5.0.0"))
    assert any("핀 불일치: django" in e for e in errors)


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


@pytest.mark.parametrize(
    ("raw", "name", "extras", "version"),
    [
        ("django==6.0.5", "django", set(), "6.0.5"),
        ("Pillow", "pillow", set(), None),
        ("django-storages[s3]==1.14.6", "django-storages", {"s3"}, "1.14.6"),
        ("boto3-stubs[s3,ec2]", "boto3-stubs", {"s3", "ec2"}, None),
    ],
)
def test_의존성_파싱(raw, name, extras, version):
    dep = check_hook_pins.parse_dep(raw)
    assert dep is not None
    assert (dep.name, set(dep.extras), dep.version) == (name, extras, version)


# ── Makefile ───────────────────────────────────────────────────────────────────


def test_Makefile_의_pre_commit_버전도_대조한다():
    errors, _ = run(makefile=MAKEFILE.replace("pre-commit==4.6.0", "pre-commit==4.0.0"))
    assert any("핀 불일치: pre-commit" in e for e in errors)


def test_Makefile_에서_설치줄이_사라지면_실패한다():
    errors, _ = run(makefile="hooks:\n\tuv tool run pre-commit install\n")
    assert any("찾지 못했습니다" in e for e in errors)


# ── 실제 저장소 파일 ───────────────────────────────────────────────────────────


def test_실제_저장소_파일이_통과한다():
    """테스트용 샘플이 아니라 지금 저장소에 있는 실제 파일로 한 번 더 확인한다."""
    errors, checked = check_hook_pins.check(
        (ROOT / ".pre-commit-config.yaml").read_text(encoding="utf-8"),
        (ROOT / "uv.lock").read_text(encoding="utf-8"),
        (ROOT / "Makefile").read_text(encoding="utf-8"),
    )
    assert errors == []
    # 줄 삭제는 이 수를 줄인다 — 이름 집합과 별개로 한 번 더 걸리게 둔다.
    expected = (
        len(check_hook_pins.REPO_TO_PACKAGE) + 1 + len(check_hook_pins.REQUIRED_PINNED)
    )
    assert checked == expected


def test_실제_설정의_이름_집합이_두_목록에_모두_등록돼_있다():
    """목록과 설정 파일이 어긋나면 게이트가 엉뚱한 것을 지키게 된다."""
    config = check_hook_pins.read_config(
        (ROOT / ".pre-commit-config.yaml").read_text(encoding="utf-8")
    )
    names = {d.name for raw in config.deps if (d := check_hook_pins.parse_dep(raw))}
    assert names == check_hook_pins.REQUIRED_PINNED | check_hook_pins.UNPINNED_ALLOWED
    assert not (check_hook_pins.REQUIRED_PINNED & check_hook_pins.UNPINNED_ALLOWED)
