from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.post import Post
from app.models.user import User
from app.repositories.focus_mode_repo import FocusModeRepository
from app.repositories.interest_repo import InterestRepository
from app.repositories.post_repo import PostRepository
from app.repositories.reaction_repo import ReactionRepository


class PostService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.posts = PostRepository(db)
        self.interests = InterestRepository(db)
        self.focus_modes = FocusModeRepository(db)
        self.reactions = ReactionRepository(db)

    # ---------- create ----------
    async def create_post(
        self, author: User, text: str, interest_slug: str, media_urls: list[str]
    ) -> Post:
        # validate interest exists
        interest = await self.interests.get_by_slug(interest_slug)
        if not interest or not interest.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown interest: {interest_slug}",
            )

        # Create post immediately with pending status — AI runs in background
        post = Post(
            author_id=author.id,
            text=text,
            interest_slug=interest_slug,
            media_urls=media_urls or [],
            ai_generated=False,
            ai_label_shown=False,
            moderation_status="pending",
            moderation_reason=None,
        )
        post = await self.posts.create(post)

        # Queue moderation task (always — every post must be moderated)
        from app.workers.tasks import evaluate_bot, moderate_post
        moderate_post.delay(post.id)

        # Bot evaluation: throttled, not on every post.
        # Run when: author's post count is a multiple of 10, OR
        #           author has posted > 5 times in the last hour (burst).
        total_posts = await self.posts.count_all_posts_by_author(author.id)
        recent_posts = await self.posts.count_recent_posts_by_author(author.id, minutes=60)

        should_evaluate = (total_posts % 10 == 0) or (recent_posts > 5)
        if should_evaluate:
            evaluate_bot.delay(author.id)

        return post
    
    

    # ---------- reads ----------
    async def get_post_or_404(self, post_id: str) -> Post:
        post = await self.posts.get(post_id)
        if not post or post.is_hidden:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Post not found",
            )
        return post

    # ---------- feed ----------
    async def build_feed(
        self, user: User, limit: int = 50, offset: int = 0
    ) -> tuple[list[Post], list[str], bool, str | None]:
        """Returns (posts, applied_slugs, focus_applied, focus_name)."""

        # 1. user's selected interests
        user_interests = await self.interests.list_user_interests(user.id)
        user_slugs = {i.slug for i in user_interests}

        if not user_slugs:
            return [], [], False, None

        # 2. active focus mode (if any)
        focus_applied = False
        focus_name = None
        effective_slugs = set(user_slugs)

        if user.active_focus_mode_id:
            mode = await self.focus_modes.get(user.active_focus_mode_id)
            if mode and mode.user_id == user.id:
                mode_slugs = set(mode.interest_slugs or [])
                effective_slugs = user_slugs & mode_slugs
                focus_applied = True
                focus_name = mode.name

        if not effective_slugs:
            return [], list(effective_slugs), focus_applied, focus_name

        # 3. fetch posts
        posts = await self.posts.list_by_interest_slugs(
            sorted(effective_slugs), limit=limit, offset=offset,for_user_id=user.id,
        )
        enriched = await self.enrich_posts_with_reactions(posts, user)
        return enriched, sorted(effective_slugs), focus_applied, focus_name

    # ---------- delete ----------
    async def delete_post(self, user: User, post_id: str) -> None:
        post = await self.get_post_or_404(post_id)
        if post.author_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only delete your own posts",
            )
        await self.posts.delete(post)
        
    async def toggle_like(self, user: User, post_id: str) -> tuple[bool, int]:
        """Toggle 'like' on a post. Returns (is_liked_now, new_count)."""
        post = await self.get_post_or_404(post_id)
        existing = await self.reactions.get(user.id, post.id, kind="like")
        if existing:
            await self.reactions.remove(user.id, post.id, kind="like")
            liked = False
        else:
            await self.reactions.add(user.id, post.id, kind="like")
            liked = True
        count = await self.reactions.count_for_post(post.id)
        return liked, count

    async def enrich_posts_with_reactions(
        self, posts: list, current_user: User
    ) -> list[dict]:
        """Attach reaction_count + is_liked_by_me to each post."""
        if not posts:
            return []
        ids = [p.id for p in posts]
        counts = await self.reactions.count_for_posts(ids)
        liked = await self.reactions.liked_post_ids(current_user.id, ids)

        out = []
        for p in posts:
            data = {
                "id": p.id,
                "author_id": p.author_id,
                "text": p.text,
                "interest_slug": p.interest_slug,
                "media_urls": p.media_urls or [],
                "ai_generated": p.ai_generated,
                "ai_label_shown": p.ai_label_shown,
                "moderation_status": p.moderation_status,
                "moderation_reason": p.moderation_reason,
                "is_hidden": p.is_hidden,
                "created_at": p.created_at,
                "updated_at": p.updated_at,
                "author": None,
                "reaction_count": counts.get(p.id, 0),
                "is_liked_by_me": p.id in liked,
            }
            out.append(data)
        return out
        