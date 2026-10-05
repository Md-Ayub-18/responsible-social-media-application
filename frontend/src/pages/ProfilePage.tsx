import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { api, ApiError } from "../lib/api";
import type {
  BlockResponse,
  FollowResponse,
  UserProfileResponse,
} from "../lib/types";
import PostCard from "../components/PostCard";
import { CardSkeleton, PostSkeleton } from "../components/Skeleton";
import TierBadge from "../components/TierBadge";
import { useAuth } from "../contexts/AuthContext";

export default function ProfilePage() {
  const { username } = useParams<{ username: string }>();
  const { user: currentUser } = useAuth();

  const [data, setData] = useState<UserProfileResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [followBusy, setFollowBusy] = useState(false);
  const [blockBusy, setBlockBusy] = useState(false);
  const [showBlockMenu, setShowBlockMenu] = useState(false);

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

  async function toggleFollow() {
    if (!data || followBusy) return;
    setFollowBusy(true);
    try {
      const isFollowing = data.profile.is_following;
      const res = await (isFollowing
        ? api.delete<FollowResponse>(
            `/api/v1/social/follow/${data.profile.username}`
          )
        : api.post<FollowResponse>(
            `/api/v1/social/follow/${data.profile.username}`
          ));

      setData({
        ...data,
        profile: {
          ...data.profile,
          is_following: res.is_following,
          follower_count: res.follower_count,
        },
      });
    } catch (err) {
      alert(err instanceof ApiError ? err.detail : "Action failed");
    } finally {
      setFollowBusy(false);
    }
  }

  async function toggleBlock() {
    if (!data || blockBusy) return;
    setBlockBusy(true);
    try {
      await api.post<BlockResponse>(`/api/v1/blocks/${data.profile.username}`);
      setShowBlockMenu(false);
      alert(
        `Blocked @${data.profile.username}. They can no longer see your content.`
      );
      window.location.reload();
    } catch (err) {
      alert(err instanceof ApiError ? err.detail : "Action failed");
    } finally {
      setBlockBusy(false);
    }
  }

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
  const isOwnProfile = currentUser?.username === profile.username;

  return (
    <div className="max-w-2xl mx-auto px-4 py-6">
      {/* Profile header */}
      <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6 mb-5">
        <div className="flex items-center gap-4">
          <div className="w-16 h-16 rounded-full bg-gradient-to-br from-sky-400 to-indigo-500 flex items-center justify-center text-white text-2xl font-bold">
            {profile.username.slice(0, 1).toUpperCase()}
          </div>
          <div className="flex-1">
            <div className="flex items-center gap-2 flex-wrap">
              <h1 className="text-2xl font-bold text-gray-900">
                {profile.display_name || profile.username}
              </h1>
              <TierBadge tier={profile.account_tier} size="md" />
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
              {profile.is_private && (
                <span className="text-xs px-2 py-0.5 rounded-full bg-gray-100 text-gray-600 border border-gray-200">
                  🔒 private
                </span>
              )}
            </div>
            <p className="text-sm text-gray-500">@{profile.username}</p>
            <p className="text-xs text-gray-400 mt-1">Joined {joined}</p>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-4 gap-4 mt-5 pt-5 border-t border-gray-100">
          <div className="text-center">
            <p className="text-xl font-bold text-gray-900">
              {profile.post_count}
            </p>
            <p className="text-xs text-gray-500 uppercase tracking-wider">
              Posts
            </p>
          </div>
          <div className="text-center">
            <p className="text-xl font-bold text-gray-900">
              {profile.follower_count}
            </p>
            <p className="text-xs text-gray-500 uppercase tracking-wider">
              Followers
            </p>
          </div>
          <div className="text-center">
            <p className="text-xl font-bold text-gray-900">
              {profile.following_count}
            </p>
            <p className="text-xs text-gray-500 uppercase tracking-wider">
              Following
            </p>
          </div>
          <div className="text-center">
            <p className="text-xl font-bold text-gray-900">
              {profile.likes_received}
            </p>
            <p className="text-xs text-gray-500 uppercase tracking-wider">
              Likes
            </p>
          </div>
        </div>

        {/* Action buttons (only if viewing someone else's profile) */}
        {!isOwnProfile && currentUser && (
          <div className="flex items-center gap-2 mt-5 pt-5 border-t border-gray-100">
            <button
              onClick={toggleFollow}
              disabled={followBusy}
              className={`text-sm px-4 py-2 rounded-lg transition-colors press ${
                profile.is_following
                  ? "border border-gray-300 text-gray-700 hover:bg-gray-50"
                  : "bg-sky-600 text-white hover:bg-sky-700"
              } disabled:opacity-50`}
            >
              {followBusy
                ? "..."
                : profile.is_following
                ? "Following"
                : "Follow"}
            </button>

            <div className="relative">
              <button
                onClick={() => setShowBlockMenu((s) => !s)}
                className="text-sm px-3 py-2 border border-gray-300 text-gray-600 rounded-lg hover:bg-gray-50"
                title="More options"
              >
                ⋯
              </button>
              {showBlockMenu && (
                <div className="absolute right-0 top-full mt-1 w-44 bg-white border border-gray-100 rounded-lg shadow-lg py-1 z-10">
                  <button
                    onClick={toggleBlock}
                    disabled={blockBusy}
                    className="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50 disabled:opacity-50"
                  >
                    🚫 Block @{profile.username}
                  </button>
                </div>
              )}
            </div>
          </div>
        )}
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