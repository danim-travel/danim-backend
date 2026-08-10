#!/usr/bin/env python
"""`.pre-commit-config.yaml` 의 버전이 `uv.lock` 과 일치하는지 검사한다.

pre-commit 훅은 uv.lock 을 읽지 못하고 설정 파일에 적힌 값으로 pip 설치한다. 두 파일이
따로 관리되므로 `uv lock` 이 돌 때마다 어긋날 수 있고, 어긋나면 "로컬 훅은 통과했는데
CI 는 실패" 또는 mypy 크래시로 이어진다(이 검사가 생긴 계기).

검사 항목
    1. 훅 저장소의 rev 가 uv.lock 의 해당 패키지 버전과 같은가
    2. additional_dependencies 의 == 고정값이 uv.lock 과 같은가
    3. 고정되지 않은 additional_dependencies 가 무엇인가 (경고, 실패는 아님)

pyyaml 을 쓰지 않는 이유: 프로젝트 의존성에 없어서, 이 검사 하나를 위해 의존성을 늘리면
검사가 막으려는 문제(수동 관리 대상 증가)를 스스로 키우게 된다. 대상 파일 구조가 단순하고
`check-yaml` 훅이 문법을 별도로 보장하므로 필요한 부분만 직접 읽는다.
"""

from __future__ import annotations

import re
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / ".pre-commit-config.yaml"
LOCK = ROOT / "uv.lock"

# 훅 저장소 URL -> uv.lock 에서 대조할 패키지 이름.
# 여기 없는 저장소(pre-commit-hooks 등)는 uv.lock 에 대응 패키지가 없어 대조 대상이 아니다.
REPO_TO_PACKAGE = {
    "https://github.com/psf/black": "black",
    "https://github.com/PyCQA/isort": "isort",
    "https://github.com/pre-commit/mirrors-mypy": "mypy",
}

_REPO_RE = re.compile(r"^\s*-\s*repo:\s*(\S+)")
_REV_RE = re.compile(r"^\s*rev:\s*(\S+)")
_DEP_RE = re.compile(r"^\s{8,}-\s*(\S+)")
_ADDITIONAL_RE = re.compile(r"^\s*additional_dependencies:")
_PIN_RE = re.compile(r"^([A-Za-z0-9._-]+)(?:\[[^\]]*\])?==(\S+)$")


def normalize(name: str) -> str:
    """PyPI 이름 정규화 — uv.lock 은 소문자·하이픈 형태로 기록한다(Pillow -> pillow)."""
    return re.sub(r"[-_.]+", "-", name).lower()


def read_lock_versions() -> dict[str, str]:
    data = tomllib.loads(LOCK.read_text())
    return {normalize(p["name"]): p["version"] for p in data.get("package", [])}


def read_config() -> tuple[dict[str, str], list[str]]:
    """(저장소 URL -> rev, additional_dependencies 목록)을 돌려준다."""
    revs: dict[str, str] = {}
    deps: list[str] = []
    current_repo: str | None = None
    in_deps = False

    for line in CONFIG.read_text().splitlines():
        if (m := _REPO_RE.match(line)) is not None:
            current_repo = m.group(1)
            in_deps = False
            continue
        if (m := _REV_RE.match(line)) is not None and current_repo:
            revs[current_repo] = m.group(1)
            continue
        if _ADDITIONAL_RE.match(line):
            in_deps = True
            continue
        if in_deps:
            if (m := _DEP_RE.match(line)) is not None:
                deps.append(m.group(1))
            elif line.strip() and not line.lstrip().startswith("#"):
                in_deps = False

    return revs, deps


def main() -> int:
    lock = read_lock_versions()
    revs, deps = read_config()

    # 파싱 실패를 통과로 오인하지 않도록 최소 개수를 확인한다.
    if not revs or not deps:
        print("[FAIL] .pre-commit-config.yaml 파싱 결과가 비었습니다. 형식을 확인하세요.")
        return 1

    errors: list[str] = []
    unpinned: list[str] = []

    for repo, package in REPO_TO_PACKAGE.items():
        rev = revs.get(repo)
        if rev is None:
            errors.append(f"rev 누락: {repo}")
            continue
        expected = lock.get(normalize(package))
        if expected is None:
            errors.append(f"uv.lock 에 {package} 가 없습니다")
            continue
        if rev.lstrip("v") != expected:
            errors.append(f"rev 불일치: {package} 훅={rev} uv.lock={expected}")

    for dep in deps:
        if (m := _PIN_RE.match(dep)) is None:
            unpinned.append(dep)
            continue
        name, version = m.group(1), m.group(2)
        expected = lock.get(normalize(name))
        if expected is None:
            errors.append(f"uv.lock 에 {name} 이 없습니다 (훅={version})")
        elif version != expected:
            errors.append(f"핀 불일치: {name} 훅={version} uv.lock={expected}")

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
        print("       uv.lock 값으로 .pre-commit-config.yaml 을 갱신하세요.")
        return 1

    checked = len(REPO_TO_PACKAGE) + (len(deps) - len(unpinned))
    print(f"[OK] 훅 설정이 uv.lock 과 일치합니다 (대조 {checked}건)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
