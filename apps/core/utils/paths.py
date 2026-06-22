from django.conf import settings


def get_artifact_dir():
    path = settings.BASE_DIR / "artifacts"
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_next_codebook_dir():
    path = get_artifact_dir() / "codebook"
    path.mkdir(parents=True, exist_ok=True)

    versions = []
    for d in path.iterdir():
        if d.is_dir() and d.name.startswith("v"):
            versions.append(int(d.name[1:]))

    next_num = max(versions) + 1 if versions else 1
    path /= f"v{next_num}"
    path.mkdir(parents=True, exist_ok=True)

    return path
