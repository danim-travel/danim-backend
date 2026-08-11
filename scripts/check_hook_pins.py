#!/usr/bin/env python
"""훅 설정에 적힌 버전이 `uv.lock` 과 일치하는지 검사한다.

pre-commit 훅은 uv.lock 을 읽지 못하고 설정 파일에 적힌 값으로 pip 설치한다. 두 파일이
따로 관리되므로 `uv lock` 이 돌 때마다 어긋날 수 있고, 어긋나면 "로컬 훅은 통과했는데
CI 는 실패" 또는 mypy 크래시로 이어진다(이 검사가 생긴 계기).

검사 항목
    1. 훅 저장소의 rev 가 uv.lock 의 해당 패키지 버전과 같은가
    2. additional_dependencies 의 == 고정값이 uv.lock 과 같은가
    3. Makefile 이 설치하는 pre-commit 버전이 uv.lock 과 같은가
    4. 매핑에 없는 훅 저장소가 새로 생기지 않았는가
    5. 읽어내지 못한 additional_dependencies 블록이 없는가
    6. 미고정 의존성 개수가 그대로인가 (MAX_UNPINNED 래칫)

4~6 번이 있는 이유: 1~3 이 실패했을 때 값을 고치는 대신 고정값을 지우거나, 저장소를
새로 추가하거나, 인라인 표기로 바꾸면 검사가 통과해버린다. 드리프트를 막으려는 검사를
드리프트로 우회하는 길이라 함께 막아둔다.

pyyaml 을 쓰지 않는 이유: 프로젝트 의존성에 없어서, 이 검사 하나를 위해 의존성을 늘리면
검사가 막으려는 문제(수동 관리 대상 증가)를 스스로 키우게 된다. 대상 파일 구조가 단순하고
`check-yaml` 훅이 문법을 별도로 보장하므로 필요한 부분만 직접 읽는다.
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

# 현재 미고정 의존성 개수. 늘어도 줄어도 실패하는 래칫이다.
#   늘어남 = 고정값을 지워 검사를 우회한 것 -> 막는다
#   줄어듦 = 새로 고정한 것 -> 이 값도 같이 낮춰 다음 우회의 기준선을 조인다
MAX_UNPINNED = 7

_REPO_RE = re.compile(r"^\s*-\s*repo:\s*(\S+)")
_REV_RE = re.compile(r"^\s*rev:\s*(\S+)")
_ADDITIONAL_RE = re.compile(r"^\s*additional_dependencies:")
_PIN_RE = re.compile(r"^([A-Za-z0-9._-]+)(?:\[[^\]]*\])?==([^\s;,=<>!~]+)$")
_MAKE_PRECOMMIT_RE = re.compile(r"uv tool install\s+pre-commit==(\S+)")


def normalize(name: str) -> str:
    """PyPI 이름 정규화 — uv.lock 은 소문자·하이픈 형태로 기록한다(Pillow -> pillow)."""
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


def check(
    config_text: str,
    lock_text: str,
    makefile_text: str,
    max_unpinned: int = MAX_UNPINNED,
) -> tuple[list[str], list[str], int]:
    """(오류 목록, 미고정 의존성 목록, 대조한 건수)를 돌려준다."""
    lock = read_lock_versions(lock_text)
    config = read_config(config_text)
    revs, deps = config.revs, config.deps

    # 파싱 실패를 통과로 오인하지 않도록 최소 개수를 확인한다.
    if not revs or not deps:
        return (
            [".pre-commit-config.yaml 파싱 결과가 비었습니다. 형식을 확인하세요."],
            [],
            0,
        )

    errors: list[str] = []
    unpinned: list[str] = []

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
        rev = revs.get(repo)
        if rev is None:
            errors.append(f"rev 누락: {repo}")
            continue
        expected, reason = resolve(lock, package)
        if expected is None:
            errors.append(str(reason))
        elif rev.lstrip("v") != expected:
            errors.append(f"rev 불일치: {package} 훅={rev} uv.lock={expected}")

    for dep in deps:
        if (m := _PIN_RE.match(dep)) is None:
            unpinned.append(dep)
            continue
        name, version = m.group(1), m.group(2)
        expected, reason = resolve(lock, name)
        if expected is None:
            errors.append(f"{reason} (훅={version})")
        elif version != expected:
            errors.append(f"핀 불일치: {name} 훅={version} uv.lock={expected}")

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

    if len(unpinned) > max_unpinned:
        errors.append(
            f"미고정 의존성이 {len(unpinned)}개로 늘었습니다 (허용 {max_unpinned}개)."
            " 고정값을 지워 검사를 우회하지 말고 uv.lock 값으로 맞추세요"
        )
    elif len(unpinned) < max_unpinned:
        errors.append(
            f"미고정 의존성이 {len(unpinned)}개로 줄었습니다 (기준 {max_unpinned}개)."
            f" check_hook_pins.py 의 MAX_UNPINNED 를 {len(unpinned)} 로 낮추세요"
        )

    checked = len(REPO_TO_PACKAGE) + 1 + (len(deps) - len(unpinned))
    return errors, unpinned, checked


def main() -> int:
    errors, unpinned, checked = check(
        CONFIG.read_text(encoding="utf-8"),
        LOCK.read_text(encoding="utf-8"),
        MAKEFILE.read_text(encoding="utf-8"),
    )

    if unpinned:
        print(f"[INFO] 미고정 의존성 {len(unpinned)}개 — 설치 시점 최신이 깔립니다.")
        for dep in unpinned:
            print(f"       - {dep}")
        print()

    if errors:
        print(f"[FAIL] 훅 설정이 uv.lock 과 어긋납니다 ({len(errors)}건)")
        for err in errors:
            print(f"       - {err}")
        print()
        print("       uv.lock 을 기준으로 훅 설정을 맞추세요.")
        return 1

    print(f"[OK] 훅 설정이 uv.lock 과 일치합니다 (대조 {checked}건)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
