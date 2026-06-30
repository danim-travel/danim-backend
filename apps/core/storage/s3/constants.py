ALLOWED_EXTENSIONS: dict[str, str] = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
}

COMMENT_ALLOWED_EXTENSIONS: dict[str, str] = {
    **ALLOWED_EXTENSIONS,
    ".gif": "image/gif",
}
