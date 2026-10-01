import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.config import settings
from app.dependencies import get_current_user
from app.models.user import User

router = APIRouter(prefix="/uploads", tags=["uploads"])


ALLOWED_IMAGE = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
ALLOWED_VIDEO = {".mp4", ".mov", ".webm"}
ALLOWED = ALLOWED_IMAGE | ALLOWED_VIDEO


@router.post("/media", status_code=status.HTTP_201_CREATED)
async def upload_post_media(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    """Upload an image or video for a post. Returns the public URL."""
    if not file.filename:
        raise HTTPException(400, "No filename provided")

    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED:
        raise HTTPException(
            400,
            f"File type {ext} not allowed. Accepted: {sorted(ALLOWED)}",
        )

    media_dir = Path(settings.MEDIA_POSTS_DIR).resolve()
    media_dir.mkdir(parents=True, exist_ok=True)

    stored_name = f"{uuid.uuid4().hex}{ext}"
    stored_path = media_dir / stored_name

    max_bytes = settings.MAX_POST_MEDIA_MB * 1024 * 1024
    size = 0
    with stored_path.open("wb") as f:
        while chunk := await file.read(1024 * 1024):
            size += len(chunk)
            if size > max_bytes:
                f.close()
                stored_path.unlink(missing_ok=True)
                raise HTTPException(
                    413,
                    f"File exceeds {settings.MAX_POST_MEDIA_MB} MB limit",
                )
            f.write(chunk)

    return {
        "url": f"/media/posts/{stored_name}",
        "kind": "image" if ext in ALLOWED_IMAGE else "video",
        "size_bytes": size,
    }