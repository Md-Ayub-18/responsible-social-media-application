from pathlib import Path

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.stitch_project import Contribution, StitchProject
from app.models.user import User
from app.repositories.interest_repo import InterestRepository
from app.repositories.stitch_repo import StitchRepository
from app.services.stitch_processor import StitchProcessor


class StitchService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = StitchRepository(db)
        self.interests = InterestRepository(db)
        self.processor = StitchProcessor()

    # ---------- projects ----------
    async def create_project(
        self,
        moderator: User,
        title: str,
        description: str | None,
        interest_slug: str,
        visibility: str = "public",
    ) -> StitchProject:
        interest = await self.interests.get_by_slug(interest_slug)
        if not interest or not interest.is_active:
            raise HTTPException(400, f"Unknown interest: {interest_slug}")

        project = StitchProject(
            moderator_id=moderator.id,
            title=title,
            description=description,
            interest_slug=interest_slug,
            status="open",
            allow_contributions=True,
            visibility=visibility,
        )
        return await self.repo.create_project(project)

    async def get_project_or_404(
        self, project_id: str, with_contributions: bool = False, as_user: User | None = None
    ) -> StitchProject:
        project = await self.repo.get_project(project_id, with_contributions)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
            )
        return project

    async def list_projects(
        self, status: str | None, interest_slug: str | None, limit: int, offset: int
    ) -> list[StitchProject]:
        return await self.repo.list_projects(status, interest_slug, limit, offset)

    async def update_project(
        self, moderator: User, project_id: str, **changes
    ) -> StitchProject:
        project = await self.get_project_or_404(project_id)
        self._require_moderator(project, moderator)
        changes = {k: v for k, v in changes.items() if v is not None}
        if not changes:
            return project
        return await self.repo.update_project(project, **changes)

    # ---------- contributions ----------
    async def submit_contribution(
        self,
        contributor: User,
        project_id: str,
        file: UploadFile,
        caption: str | None,
        consent_given: bool,
    ) -> Contribution:
        project = await self.get_project_or_404(project_id)

        if not project.allow_contributions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Contributions are currently closed for this project",
            )
        if project.status not in ("open", "in_review"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot contribute to a project in status '{project.status}'",
            )
        if not consent_given:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Consent is required to submit a contribution",
            )
        if not file.filename or not file.filename.lower().endswith((".mp4", ".mov", ".webm")):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only .mp4, .mov, .webm files are accepted",
            )

        # Save the file
        uploads_dir = Path(settings.MEDIA_UPLOADS_DIR).resolve()
        uploads_dir.mkdir(parents=True, exist_ok=True)

        import uuid
        ext = Path(file.filename).suffix.lower()
        stored_name = f"{uuid.uuid4().hex}{ext}"
        stored_path = uploads_dir / stored_name

        size_bytes = 0
        max_bytes = settings.MAX_UPLOAD_MB * 1024 * 1024
        with stored_path.open("wb") as f:
            while chunk := await file.read(1024 * 1024):
                size_bytes += len(chunk)
                if size_bytes > max_bytes:
                    f.close()
                    stored_path.unlink(missing_ok=True)
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"File exceeds {settings.MAX_UPLOAD_MB} MB limit",
                    )
                f.write(chunk)



        contribution = Contribution(
            project_id=project.id,
            contributor_id=contributor.id,
            video_url=f"/media/uploads/{stored_name}",
            caption=caption,
            duration_seconds=None,
            consent_given=True,
            status="pending",
        )
        return await self.repo.create_contribution(contribution)

    async def list_contributions(self, project_id: str) -> list[Contribution]:
        await self.get_project_or_404(project_id)
        return await self.repo.list_contributions(project_id)

    async def moderate_contribution(
        self,
        moderator: User,
        contribution_id: str,
        new_status: str,
        rejection_reason: str | None,
        order_index: int | None,
    ) -> Contribution:
        contribution = await self.repo.get_contribution(contribution_id)
        if not contribution:
            raise HTTPException(404, "Contribution not found")

        project = await self.get_project_or_404(contribution.project_id)
        self._require_moderator(project, moderator)

        if not contribution.consent_given:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot moderate a contribution without consent",
            )

        if new_status == "approved":
            return await self.repo.update_contribution(
                contribution, status="approved",
                rejection_reason=None, order_index=order_index,
            )
        else:  # rejected
            return await self.repo.update_contribution(
                contribution, status="rejected",
                rejection_reason=rejection_reason or "Rejected by moderator",
                order_index=None,
            )

    async def withdraw_contribution(self, user: User, contribution_id: str) -> None:
        contribution = await self.repo.get_contribution(contribution_id)
        if not contribution:
            raise HTTPException(404, "Contribution not found")

        project = await self.get_project_or_404(contribution.project_id)

        # contributor can withdraw their own; moderator can remove any
        if user.id != contribution.contributor_id and user.id != project.moderator_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You cannot remove this contribution",
            )

        await self.repo.delete_contribution(contribution)

    # ---------- stitch ----------
    async def stitch_project(self, moderator: User, project_id: str) -> StitchProject:
        project = await self.get_project_or_404(project_id)
        self._require_moderator(project, moderator)

        if project.status == "stitched":
            raise HTTPException(400, "Project is already stitched")

        approved = await self.repo.list_approved_contributions(project_id)
        if not approved:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No approved contributions to stitch",
            )

        # Map contribution URLs → filenames
        filenames = []
        for c in approved:
            # video_url looks like "/media/uploads/<filename>"
            name = c.video_url.rsplit("/", 1)[-1]
            filenames.append(name)

        try:
            output_url = self.processor.stitch(project_id, filenames)
        except Exception as e:
            await self.repo.update_project(
                project, status="in_review", stitch_error=str(e)[:500]
            )
            raise HTTPException(500, f"Stitching failed: {e}")

        return await self.repo.update_project(
            project,
            status="stitched",
            stitched_video_url=output_url,
            stitch_error=None,
            allow_contributions=False,
        )

    # ---------- permissions ----------
    @staticmethod
    def _require_moderator(project: StitchProject, user: User) -> None:
        if project.moderator_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the project moderator can perform this action",
            )
    async def _can_view_project(self, user: User, project: StitchProject) -> bool:
        """Returns True if the user has permission to view this project."""
        # Public — anyone
        if project.visibility == "public":
            return True

        # The moderator always has access
        if project.moderator_id == user.id:
            return True

        # Private — only the moderator (already checked) and approved contributors
        if project.visibility == "private":
            contributions = await self.repo.list_contributions(project.id)
            return any(c.contributor_id == user.id for c in contributions)

        # Community — anyone with the same interest OR a member of a community
        # with that interest
        if project.visibility == "community":
            # Check the user's selected interests
            user_interests = await self.interests.list_user_interests(user.id)
            if any(i.slug == project.interest_slug for i in user_interests):
                return True

            # Check community membership with that interest
            from app.repositories.community_repo import CommunityRepository
            communities = await CommunityRepository(self.db).list_user_communities(user.id)
            return any(c.interest_slug == project.interest_slug for c in communities)

        return False
    
    async def list_visible_projects(
        self, user: User, status: str | None, interest_slug: str | None,
        limit: int, offset: int,
    ) -> list[StitchProject]:
        all_projects = await self.repo.list_projects(status, interest_slug, limit, offset)
        visible = []
        for p in all_projects:
            if await self._can_view_project(user, p):
                visible.append(p)
        return visible


