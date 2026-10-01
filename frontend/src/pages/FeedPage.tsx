import { useEffect, useState } from "react";
import { api, ApiError } from "../lib/api";
import type { FeedResponse } from "../lib/types";
import PostCard from "../components/PostCard";
import FocusModeBanner from "../components/FocusModeBanner";
import { FeedSkeleton } from "../components/Skeleton";

export default function FeedPage() {
  const [feed, setFeed] = useState<FeedResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setLoading(true);
      setError(null);
      try {
        const data = await api.get<FeedResponse>("/api/v1/feed?limit=30");
        if (!cancelled) setFeed(data);
      } catch (err) {
        if (!cancelled) {
          const msg =
            err instanceof ApiError
              ? typeof err.detail === "string"
                ? err.detail
                : "Failed to load feed"
              : "Failed to load feed";
          setError(msg);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, []);

  function handleLikeChange(postId: string, liked: boolean, count: number) {
    setFeed((prev) => {
      if (!prev) return prev;
      return {
        ...prev,
        posts: prev.posts.map((p) =>
          p.id === postId
            ? { ...p, is_liked_by_me: liked, reaction_count: count }
            : p
        ),
      };
    });
  }

  return (
    <div className="max-w-2xl mx-auto px-4 py-6">
      <h1 className="text-2xl font-bold text-gray-900 mb-5">Your feed</h1>

      {loading && <FeedSkeleton />}

      {error && (
        <div className="bg-red-50 border border-red-100 text-red-700 rounded-xl p-4 text-sm">
          {error}
        </div>
      )}

      {!loading && !error && feed && (
        <>
          <FocusModeBanner
            modeName={feed.focus_mode_name}
            focusApplied={feed.focus_mode_applied}
            interestSlugs={feed.applied_interest_slugs}
          />

          {feed.posts.length === 0 ? (
            <div className="text-center py-16 text-gray-400">
              <p className="text-4xl mb-3">🕊️</p>
              <p>No posts to show here yet.</p>
              <p className="text-xs mt-2">
                Try selecting more interests or switching focus modes.
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {feed.posts.map((post) => (
                <PostCard
                  key={post.id}
                  post={post}
                  onLikeChange={handleLikeChange}
                />
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}