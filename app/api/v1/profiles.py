from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.age_utils import classify_account
from app.db.session import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.repositories.profile_repo import ProfileRepository
from app.schemas.profile import PublicProfile, UserProfileResponse
from app.services.post_service import PostService

router = APIRouter(prefix="/users", tags=["profiles"])


@router.get("/{username}", response_model=UserProfileResponse)
async def get_profile(
    username: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Public profile with stats + recent posts."""
    repo = ProfileRepository(db)
    user = await repo.get_user_by_username(username)
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")

    post_count = await repo.count_user_posts(user.id)
    likes_received = await repo.count_likes_received(user.id)
    posts = await repo.list_user_posts(user.id, limit=30)

    profile = PublicProfile.model_validate(user)
    profile.post_count = post_count
    profile.likes_received = likes_received
    if user.date_of_birth:
        profile.account_tier = classify_account(user.date_of_birth)

    # enrich posts with reactions & author
    post_service = PostService(db)
    enriched = await post_service.enrich_posts_with_reactions(posts, current_user)

    return UserProfileResponse(profile=profile, posts=enriched)
