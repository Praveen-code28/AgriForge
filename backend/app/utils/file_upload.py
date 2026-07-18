import json
import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile, status

ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}


def validate_image_upload(file: UploadFile, max_bytes: int) -> str:
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported image type: {file.content_type}",
        )

    ext_map = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}
    ext = ext_map[file.content_type]
    safe_name = f"{uuid.uuid4().hex}{ext}"
    return safe_name


async def save_upload(file: UploadFile, upload_dir: Path, max_bytes: int) -> tuple[str, Path]:
    safe_name = validate_image_upload(file, max_bytes)
    upload_dir.mkdir(parents=True, exist_ok=True)
    dest = upload_dir / safe_name

    content = await file.read()
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Image exceeds maximum upload size",
        )
    dest.write_bytes(content)
    return safe_name, dest


def dumps_json(data: object) -> str:
    return json.dumps(data, default=str)
