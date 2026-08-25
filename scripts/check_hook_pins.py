#!/usr/bin/env python
"""훅 설정에 적힌 버전이 `uv.lock` 과 일치하는지 검사한다.

pre-commit 훅은 uv.lock 을 읽지 못하고 설정 파일에 적힌 값으로 pip 설치한다. 두 파일이
따로 관리되므로 `uv lock` 이 돌 때마다 어긋날 수 있고, 어긋나면 "로컬 훅은 통과했는데
CI 는 실패" 또는 mypy 크래시로 이어진다(이 검사가 생긴 계기).

검사 항목
    1. 훅 저장소의 rev 가 uv.lock 의 해당 패키지 버전과 같은가
    2. additional_dependencies 의 == 고정값이 uv.lock 과 같은가
    3. uv.lock 이 요구하는 extra 가 훅 설정에도 붙어 있는가
    4. Makefile 이 설치하는 pre-commit 버전이 uv.lock 과 같은가
    5. 매핑에 없는 훅 저장소가 새로 생기지 않았는가
    6. 읽어내지 못한 additional_dependencies 블록이 없는가
    7. 있어야 할 의존성이 전부 있고, 고정돼야 할 것이 고정돼 있는가 (이름 집합)

7 번이 개수가 아니라 **이름 집합**인 이유: 개수 래칫은 "미고정이 N개인가" 만 보므로,
줄을 통째로 지우거나 주석 처리하거나 다른 항목과 맞바꾸면 개수가 그대로라 통과한다.
그리고 줄 삭제는 `==` 제거보다 나쁘다 — 그 패키지가 훅 env 에 아예 설치되지 않아
django-stubs 플러그인의 `django.setup()` 이 ImportError 로 죽거나, 스텁이 extra 없이
떠서 이 검사가 막으려던 mypy INTERNAL ERROR 가 그대로 재발한다.

pyyaml 을 쓰지 않는 이유: uv.lock 에 pyyaml 이 있긴 하지만 pre-commit 이 끌고 온
**전이 의존**이라 직접 의존처럼 기대면 안 된다. pre-commit 을 걷어내거나 그쪽 의존이
바뀌면 조용히 사라진다. 대상 파일 구조가 단순하고 `check-yaml` 훅이 문법을 따로
보장하므로 필요한 부분만 직접 읽는다.
"""

from __future__ import annotations

import re
import sys
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / ".pre-commit-config.yaml"
LOCK = ROOT / "uv.lock"
MAKEFILE = ROOT / "Makefile"

# 훅 저장소 URL -> uv.lock 에서 대조할 패키지 이름.
REPO_TO_PACKAGE = {
    "https://github.com/psf/black": "black",
    "https://github.com/PyCQA/isort": "isort",
    "https://github.com/pre-commit/mirrors-mypy": "mypy",
}

# uv.lock 에 대응 패키지가 없어 대조할 수 없는 저장소. 여기에도 REPO_TO_PACKAGE 에도
# 없는 저장소가 설정에 나타나면 실패시킨다 — 새 훅이 조용히 검사 밖에 놓이지 않도록.
UNCHECKABLE_REPOS = {
    "https://github.com/pre-commit/pre-commit-hooks",  # uv.lock 에 없는 훅 전용 패키지
}

# 반드시 == 로 고정돼 있어야 하는 패키지. django.setup() 경로(INSTALLED_APPS·settings
# 모듈 레벨 임포트)에 있거나 스텁이라, 버전이 갈리면 타입체크 결과가 달라진다.
REQUIRED_PINNED = {
    "python-ulid",
    "django",
    "django-stubs",
    "django-stubs-ext",
    "djangorestframework-stubs",
    "daphne",
    "channels",
    "djangorestframework",
    "djangorestframework-simplejwt",
    "django-allauth",
    "dj-rest-auth",
    "django-cors-headers",
    "django-storages",
    "drf-spectacular",
    "django-redis",
    "boto3",
    "boto3-stubs",
    "mypy-boto3-s3",
    "pgvector",
}

# 고정하지 않아도 되는 패키지. 수동 관리 대상을 늘리지 않으려고 남겨 둔 것들이라
# 버전은 묻지 않되, 목록에서 사라지는 것 자체는 막는다.
UNPINNED_ALLOWED = {
    "django-environ",
    "channels-redis",
    "psycopg2-binary",
    "pillow",
    "httpx",
    "sentry-sdk",
    "celery",
}

_REPO_RE = re.compile(r"^\s*-\s*repo:\s*(\S+)")
_REV_RE = re.compile(r"^\s*rev:\s*(\S+)")
_ADDITIONAL_RE = re.compile(r"^\s*additional_dependencies:")
_DEP_RE = re.compile(r"^([A-Za-z0-9._-]+)(?:\[([^\]]*)\])?(?:==([^\s;,=<>!~]+))?$")
_MAKE_PRECOMMIT_RE = re.compile(r"uv tool install\s+pre-commit==(\S+)")


def normalize(name: str) -> str:
    """PyPI 이름 정규화(PEP 503) — uv.lock 은 소문자·하이픈으로 쓴다(Pillow -> pillow)."""
    return re.sub(r"[-_.]+", "-", name).lower()


def clean_dep(raw: str) -> str:
    """의존성 표기에서 주석·따옴표·내부 공백을 제거한다.

    공백을 지우는 이유: `pkg == 1.0` 처럼 띄어 쓴 표기가 "고정 안 됨" 으로 잘못 분류되면
    검사에서 빠져버린다. 요구사항 표기 안의 공백은 의미가 없으므로 지워도 안전하다.
    """
    raw = raw.split("#", 1)[0].strip()
    if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in "\"'":
        raw = raw[1:-1]
    return re.sub(r"\s+", "", raw)


@dataclass(frozen=True)
class Dep:
    """훅 설정의 의존성 한 줄."""

    name: str  # 정규화된 이름
    extras: frozenset[str]
    version: str | None  # == 고정값. 없으면 None


def parse_dep(dep: str) -> Dep | None:
    """`pkg[extra]==1.0` 을 뜯는다. 이해하지 못한 표기는 None(호출부에서 실패시킨다)."""
    m = _DEP_RE.match(dep)
    if m is None:
        return None
    raw_extras = m.group(2) or ""
    extras = frozenset(normalize(e) for e in raw_extras.split(",") if e.strip())
    return Dep(normalize(m.group(1)), extras, m.group(3))


def read_lock_versions(text: str) -> dict[str, set[str]]:
    """패키지 이름 -> 버전 집합. uv.lock 은 같은 이름을 여러 번 기록할 수 있다.

    (예: torch 는 PyPI 판과 +cpu 판이 따로 올라간다.) 하나로 뭉개면 대조 대상 패키지가
    중복됐을 때 임의의 값과 비교하게 되므로 집합으로 두고 호출부에서 판단한다.
    """
    data = tomllib.loads(text)
    versions: dict[str, set[str]] = {}
    for package in data.get("package", []):
        versions.setdefault(normalize(package["name"]), set()).add(package["version"])
    return versions


def read_lock_extras(text: str) -> tuple[dict[str, frozenset[str]], str | None]:
    """프로젝트가 요구하는 extra 를 uv.lock 에서 뽑는다 ((패키지 -> {extra}), 오류).

    하드코딩하지 않는 이유: pyproject 에서 extra 를 붙이거나 떼면 uv.lock 이 따라 바뀌므로
    여기서 읽으면 목록이 저절로 따라온다. `django-stubs[compatible-mypy]` 처럼 extra 가
    빠지면 mypy 버전 제약이 통째로 비활성화돼 INTERNAL ERROR 가 재발하는 자리가 있다.

    프로젝트 자신은 이름이 아니라 `source = { virtual = "." }` 로 찾는다 — 이름으로 찾으면
    패키지명을 바꿨을 때 아무 extra 도 못 읽고 조용히 통과한다.
    """
    data = tomllib.loads(text)
    extras: dict[str, frozenset[str]] = {}
    found_project = False

    for package in data.get("package", []):
        source = package.get("source", {})
        if not ({"virtual", "editable"} & source.keys()):
            continue
        found_project = True
        metadata = package.get("metadata", {})
        groups: list[list[dict]] = [metadata.get("requires-dist", [])]
        groups.extend(metadata.get("requires-dev", {}).values())
        for reqs in groups:
            for req in reqs:
                if req.get("extras"):
                    name = normalize(req["name"])
                    declared = frozenset(normalize(e) for e in req["extras"])
                    extras[name] = extras.get(name, frozenset()) | declared

    if not found_project:
        return {}, "uv.lock 에서 프로젝트 자신을 찾지 못해 extra 를 대조할 수 없습니다"
    return extras, None


@dataclass
class HookConfig:
    """훅 설정에서 읽어낸 것들."""

    repos: list[str] = field(default_factory=list)  # 등장한 모든 repo (rev 유무와 무관)
    revs: dict[str, str] = field(default_factory=dict)
    deps: list[str] = field(default_factory=list)
    empty_dep_blocks: int = 0  # 항목을 하나도 못 읽은 additional_dependencies


def read_config(text: str) -> HookConfig:
    config = HookConfig()
    current_repo: str | None = None
    deps_indent: int | None = None
    collected = 0

    def close_block() -> None:
        nonlocal deps_indent
        if deps_indent is not None and collected == 0:
            config.empty_dep_blocks += 1
        deps_indent = None

    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        indent = len(line) - len(line.lstrip())

        # additional_dependencies 블록은 키보다 깊이 들여쓴 리스트 항목까지다.
        if deps_indent is not None:
            if indent > deps_indent and stripped.startswith("- "):
                config.deps.append(clean_dep(stripped[2:]))
                collected += 1
                continue
            close_block()  # 이 줄은 아래 일반 규칙으로 다시 본다

        if (m := _REPO_RE.match(line)) is not None:
            current_repo = m.group(1)
            config.repos.append(current_repo)
        elif (m := _REV_RE.match(line)) is not None and current_repo:
            config.revs[current_repo] = m.group(1)
        elif _ADDITIONAL_RE.match(line) is not None:
            deps_indent = indent
            collected = 0

    close_block()
    return config


def resolve(lock: dict[str, set[str]], name: str) -> tuple[str | None, str | None]:
    """uv.lock 에서 단일 버전을 찾는다. 실패하면 (None, 사유)."""
    found = lock.get(normalize(name))
    if not found:
        return None, f"uv.lock 에 {name} 이(가) 없습니다"
    if len(found) > 1:
        joined = ", ".join(sorted(found))
        return None, f"uv.lock 에 {name} 이(가) 여러 버전으로 있습니다: {joined}"
    return next(iter(found)), None


def check_membership(
    pinned: set[str],
    unpinned: set[str],
    required: set[str],
    allowed: set[str],
) -> list[str]:
    """이름 집합 대조 — 개수가 아니라 "무엇이" 있어야 하는지를 지킨다."""
    errors: list[str] = []

    if gone := sorted(required - pinned - unpinned):
        errors.append(
            f"의존성 목록에서 사라진 고정 대상: {gone}"
            " — 줄을 지워 검사를 빠져나가지 마세요. 훅 env 에 설치되지 않습니다"
        )
    if demoted := sorted(required & unpinned):
        errors.append(f"고정이 풀린 패키지: {demoted} — uv.lock 값으로 == 고정하세요")
    if vanished := sorted(allowed - pinned - unpinned):
        errors.append(f"의존성 목록에서 사라진 항목: {vanished}")
    if unknown := sorted((pinned | unpinned) - required - allowed):
        errors.append(
            f"목록에 없는 의존성: {unknown}"
            " — check_hook_pins.py 의 REQUIRED_PINNED 또는 UNPINNED_ALLOWED 에 등록하세요"
        )
    return errors


def check(
    config_text: str,
    lock_text: str,
    makefile_text: str,
    required: set[str] | None = None,
    allowed: set[str] | None = None,
) -> tuple[list[str], int]:
    """(오류 목록, 대조한 건수)를 돌려준다."""
    required = REQUIRED_PINNED if required is None else required
    allowed = UNPINNED_ALLOWED if allowed is None else allowed
    lock = read_lock_versions(lock_text)
    lock_extras, extras_error = read_lock_extras(lock_text)
    config = read_config(config_text)

    # 파싱 실패를 통과로 오인하지 않도록 최소 개수를 확인한다.
    if not config.revs or not config.deps:
        return ([".pre-commit-config.yaml 파싱 결과가 비었습니다. 형식을 확인하세요."], 0)

    errors: list[str] = []
    if extras_error:
        errors.append(extras_error)

    # 인라인 표기(`additional_dependencies: [a, b]`) 등으로 항목을 못 읽으면 그 훅의
    # 고정값이 통째로 검사에서 빠진다. 조용히 넘기지 않는다.
    if config.empty_dep_blocks:
        errors.append(
            f"항목을 읽지 못한 additional_dependencies 블록 {config.empty_dep_blocks}개"
            " — 한 줄에 하나씩 `- 패키지==버전` 형태로 적어야 검사할 수 있습니다"
        )

    for repo in config.repos:
        if repo not in REPO_TO_PACKAGE and repo not in UNCHECKABLE_REPOS:
            errors.append(
                f"매핑 없는 훅 저장소: {repo}"
                " — check_hook_pins.py 의 REPO_TO_PACKAGE 또는 UNCHECKABLE_REPOS 에 등록하세요"
            )

    for repo, package in REPO_TO_PACKAGE.items():
        rev = config.revs.get(repo)
        if rev is None:
            errors.append(f"rev 누락: {repo}")
            continue
        expected, reason = resolve(lock, package)
        if expected is None:
            errors.append(str(reason))
        elif rev.lstrip("v") != expected:
            errors.append(f"rev 불일치: {package} 훅={rev} uv.lock={expected}")

    pinned: set[str] = set()
    unpinned: set[str] = set()

    for raw in config.deps:
        dep = parse_dep(raw)
        if dep is None:
            errors.append(f"이해할 수 없는 의존성 표기: {raw!r}")
            continue

        # uv.lock 이 extra 를 요구하면 훅에도 붙어 있어야 한다. 빠지면 그 extra 가 거는
        # 제약(예: compatible-mypy 의 mypy 버전 범위)이 통째로 사라진다.
        if missing := sorted(lock_extras.get(dep.name, frozenset()) - dep.extras):
            errors.append(
                f"extra 누락: {dep.name}{missing} — uv.lock 이 요구하는 extra 입니다"
            )

        if dep.version is None:
            unpinned.add(dep.name)
            continue
        pinned.add(dep.name)
        expected, reason = resolve(lock, dep.name)
        if expected is None:
            errors.append(f"{reason} (훅={dep.version})")
        elif dep.version != expected:
            errors.append(f"핀 불일치: {dep.name} 훅={dep.version} uv.lock={expected}")

    errors.extend(check_membership(pinned, unpinned, required, allowed))

    # Makefile 의 `make hooks` 는 pre-commit 자체 버전을 따로 적는 세 번째 출처다.
    if (m := _MAKE_PRECOMMIT_RE.search(makefile_text)) is None:
        errors.append(
            "Makefile 에서 `uv tool install pre-commit==...` 을 찾지 못했습니다"
        )
    else:
        expected, reason = resolve(lock, "pre-commit")
        if expected is None:
            errors.append(str(reason))
        elif m.group(1) != expected:
            errors.append(
                f"핀 불일치: pre-commit Makefile={m.group(1)} uv.lock={expected}"
            )

    checked = len(REPO_TO_PACKAGE) + 1 + len(pinned)
    return errors, checked


def main() -> int:
    errors, checked = check(
        CONFIG.read_text(encoding="utf-8"),
        LOCK.read_text(encoding="utf-8"),
        MAKEFILE.read_text(encoding="utf-8"),
    )

    if errors:
        print(f"[FAIL] 훅 설정이 uv.lock 과 어긋납니다 ({len(errors)}건)")
        for err in errors:
            print(f"       - {err}")
        print()
        print("       uv.lock 을 기준으로 훅 설정을 맞추세요.")
        return 1

    print(
        f"[OK] 훅 설정이 uv.lock 과 일치합니다 (버전 대조 {checked}건,"
        f" 고정 {len(REQUIRED_PINNED)}건 · 미고정 {len(UNPINNED_ALLOWED)}건 확인)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
