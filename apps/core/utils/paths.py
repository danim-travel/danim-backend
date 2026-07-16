import re

from django.conf import settings

# "v" + 숫자만 버전 디렉토리로 인정한다.
# startswith("v") + int(name[1:])는 v1_backup 같은 수동 디렉토리 하나에
# ValueError로 커맨드 전체가 죽는다.
_VERSION_RE = re.compile(r"^v(\d+)$")


def get_artifact_dir():
    path = settings.BASE_DIR / "artifacts"
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_next_codebook_dir():
    path = get_artifact_dir() / "codebook"
    path.mkdir(parents=True, exist_ok=True)

    versions = []
    for d in path.iterdir():
        m = _VERSION_RE.match(d.name)
        if d.is_dir() and m:
            versions.append(int(m.group(1)))

    next_num = max(versions) + 1 if versions else 1
    path /= f"v{next_num}"
    path.mkdir(parents=True, exist_ok=True)

    return path


def get_latest_codebook_dir():
    """codebook.npy가 실제로 존재하는 최신 버전 디렉토리를 반환한다.

    빈 버전 디렉토리(중단된 베이크, 과거 임포트 부작용의 잔재)를 최신으로
    인식하면 load_codewords가 매일 실패하고 update_user_taste가 통째로
    스킵되므로, "사용 가능한" 버전만 후보로 삼는다.
    """
    path = get_artifact_dir() / "codebook"
    if not path.exists():
        return None

    versions = []
    for d in path.iterdir():
        m = _VERSION_RE.match(d.name)
        if d.is_dir() and m and (d / "codebook.npy").exists():
            versions.append(int(m.group(1)))

    if not versions:
        return None

    latest_num = max(versions)
    return path / f"v{latest_num}"


def get_latest_codebook_version():
    d = get_latest_codebook_dir()
    return d.name if d else None
