import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { api, ApiError } from "../lib/api";
import type { UserProfileResponse } from "../lib/types";
import PostCard from "../components/PostCard";
import { CardSkeleton, PostSkeleton } from "../components/Skeleton";

export default function ProfilePage() {
  const { username } = useParams<{ username: string }>();
  const [data, setData] = useState<UserProfileResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!username) return;
    let cancelled = false;
    setLoading(true);
    setError(null);
    api
      .get<UserProfileResponse>(`/api/v1/users/${username}`)
      .then((d) => {
        if (!cancelled) setData(d);
      })
      .catch((err) => {
        if (!cancelled) {
          setError(
            err instanceof ApiError
              ? typeof err.detail === "string"
                ? err.detail
                : "Failed to load profile"
              : "Failed to load profile"
          );
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [username]);

  if (loading) {
  return (
    <div className="max-w-2xl mx-auto px-4 py-6">
      <CardSkeleton />
      <div className="mt-5 space-y-4">
        <PostSkeleton />
        <PostSkeleton />
      </div>
    </div>
  );
}
  if (error || !data) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-6">
        <div className="bg-red-50 border border-red-100 text-red-700 rounded-xl p-4 text-sm">
          {error ?? "Profile not found"}
        </div>
      </div>
    );
  }

  const { profile, posts } = data;
  const joined = new Date(profile.created_at).toLocaleDateString(undefined, {
    year: "numeric",
    month: "long",
  });

  return (
    <div className="max-w-2xl mx-auto px-4 py-6">
      {/* Profile header */}
      <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6 mb-5">
        <div className="flex items-center gap-4">
          {/* Avatar placeholder */}
          <div className="w-16 h-16 rounded-full bg-gradient-to-br from-sky-400 to-indigo-500 flex items-center justify-center text-white text-2xl font-bold">
            {profile.username.slice(0, 1).toUpperCase()}
          </div>
          <div className="flex-1">
            <div className="flex items-center gap-2">
              <h1 className="text-2xl font-bold text-gray-900">
                {profile.display_name || profile.username}
              </h1>
              {profile.is_moderator && (
                <span className="text-xs px-2 py-0.5 rounded-full bg-sky-50 text-sky-700 border border-sky-100">
                  moderator
                </span>
              )}
              {profile.is_child_account && (
                <span className="text-xs px-2 py-0.5 rounded-full bg-green-50 text-green-700 border border-green-100">
                  child-safe
                </span>
              )}
            </div>
            <p className="text-sm text-gray-500">@{profile.username}</p>
            <p className="text-xs text-gray-400 mt-1">Joined {joined}</p>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 gap-4 mt-5 pt-5 border-t border-gray-100">
          <div className="text-center">
            <p className="text-2xl font-bold text-gray-900">{profile.post_count}</p>
            <p className="text-xs text-gray-500 uppercase tracking-wider">Posts</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold text-gray-900">{profile.likes_received}</p>
            <p className="text-xs text-gray-500 uppercase tracking-wider">Likes received</p>
          </div>
        </div>
      </div>

      {/* Posts */}
      <h2 className="text-lg font-semibold text-gray-900 mb-3">Posts</h2>
      {posts.length === 0 ? (
        <div className="text-center py-16 text-gray-400">
          <p className="text-4xl mb-2">📝</p>
          <p className="text-sm">No posts yet.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {posts.map((post) => (
            <PostCard key={post.id} post={post} />
          ))}
        </div>
      )}
    </div>
  );
}