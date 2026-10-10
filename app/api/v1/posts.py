from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Request
from app.core.rate_limit import limiter
from fastapi import Response

from app.db.session import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.post import (
    FeedResponse,
    PostCreate,
    PostReadWithAuthor,
    ReactionToggleResponse,
)
from app.services.post_service import PostService

router = APIRouter(tags=["posts"])


@router.post("/posts", response_model=PostReadWithAuthor, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def create_post(
    request: Request,
    response: Response,
    payload: PostCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = PostService(db)
    post = await service.create_post(
        author=current_user,
        text=payload.text,
        interest_slug=payload.interest_slug,
        media_urls=payload.media_urls,
        community_id=payload.community_id,
    )
    enriched = await service.enrich_posts_with_reactions([post], current_user)
    return enriched[0]


@router.get("/posts/{post_id}", response_model=PostReadWithAuthor)
async def get_post(
    post_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = PostService(db)
    post = await service.get_post_or_404(post_id)
    enriched = await service.enrich_posts_with_reactions([post], current_user)
    return enriched[0]


@router.delete("/posts/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(
    post_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = PostService(db)
    await service.delete_post(current_user, post_id)


@router.post("/posts/{post_id}/like", response_model=ReactionToggleResponse)
async def toggle_like(
    post_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = PostService(db)
    liked, count = await service.toggle_like(current_user, post_id)
    return ReactionToggleResponse(post_id=post_id, is_liked=liked, reaction_count=count)


@router.get("/feed", response_model=FeedResponse)
async def get_feed(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = PostService(db)
    posts, applied_slugs, focus_applied, focus_name = await service.build_feed(
        current_user, limit=limit, offset=offset
    )
    return FeedResponse(
        posts=posts,
        count=len(posts),
        applied_interest_slugs=applied_slugs,
        focus_mode_applied=focus_applied,
        focus_mode_name=focus_name,
    )
