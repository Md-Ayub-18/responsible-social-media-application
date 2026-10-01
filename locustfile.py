"""
Load test for the Interest Social Platform.

Simulates N concurrent users who:
1. Log in (get JWT)
2. Read their feed
3. Read their focus modes
4. Create a post
5. Read the moderation queue (occasionally)

Run:  locust -f locustfile.py --host http://127.0.0.1:8000
Then open http://localhost:8089
"""

import random
import uuid

from locust import HttpUser, between, task


SAMPLE_TEXTS = [
    "Just finished a great tutorial on async Python.",
    "The new SQLAlchemy 2.0 typed API is a big upgrade.",
    "Sketching a new concept in Procreate this evening.",
    "Watched an incredible comeback last night.",
    "Rewatched Blade Runner 2049. Cinematography holds up.",
    "Small win: shipped a feature I'd been avoiding.",
    "Volunteered at a cleanup — 40 lbs of trash collected.",
    "Reading 'Designing Data-Intensive Applications'.",
    "Building a FastAPI app for the first time. Elegant DI.",
    "Color theory is basically cheating once you get it.",
]

INTERESTS = ["technology", "art", "learning", "sports", "entertainment", "personal", "social_causes"]


class PlatformUser(HttpUser):
    """A single simulated user."""

    wait_time = between(0.1, 0.5)  # short pauses → higher load

    def on_start(self):
        """Called once per user when they start. Register + login."""
        # Try to register; if user exists, ignore (409)
        suffix = uuid.uuid4().hex[:8]
        self.username = f"loaduser_{suffix}"
        self.email = f"{self.username}@example.com"

        self.client.post(
            "/api/v1/auth/register",
            json={
                "email": self.email,
                "username": self.username,
                "display_name": f"Load {suffix}",
                "password": "loadtest123",
            },
        )

        # Now log in (works for both fresh and existing)
        resp = self.client.post(
            "/api/v1/auth/login",
            json={"email": self.email, "password": "loadtest123"},
        )
        if resp.status_code == 200:
            self.token = resp.json()["access_token"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            self.token = None
            self.headers = {}

        # Pick two interests (ignore 409 if already selected)
        for slug in random.sample(INTERESTS, 2):
            self.client.post(
                "/api/v1/users/me/interests",
                json={"slug": slug},
                headers=self.headers,
            )

    @task(5)
    def read_feed(self):
        """Most common action — users scroll their feed."""
        self.client.get("/api/v1/feed?limit=20", headers=self.headers)

    @task(2)
    def read_focus_modes(self):
        self.client.get("/api/v1/users/me/focus-modes", headers=self.headers)

    @task(1)
    def create_post(self):
        """Post creation — previously slow, now fast."""
        text = random.choice(SAMPLE_TEXTS)
        slug = random.choice(INTERESTS)
        self.client.post(
            "/api/v1/posts",
            json={"text": text, "interest_slug": slug, "media_urls": []},
            headers=self.headers,
        )

    @task(1)
    def health_check(self):
        """Unrelated endpoint — proves nothing else is blocked."""
        self.client.get("/health")