import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api, ApiError } from "../lib/api";
import type { Community, JoinLeaveResponse, Post } from "../lib/types";
import PostCard from "../components/PostCard";

export default function CommunityDetailPage() {
  const { slug } = useParams<{ slug: string }>();
  const [community, setCommunity] = useState<Community | null>(null);
  const [posts, setPosts] = useState<Post[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function load() {
    if (!slug) return;
    setLoading(true);
    setError(null);
    try {
      const [detail, communityPosts] = await Promise.all([
        api.get<Community>(`/api/v1/communities/${slug}`),
        api.get<Post[]>(`/api/v1/communities/${slug}/posts`),
      ]);
      setCommunity(detail);
      setPosts(communityPosts);
    } catch (err) {
      setError(
        err instanceof ApiError
          ? typeof err.detail === "string"
            ? err.detail
            : "Failed to load community"
          : "Failed to load community"
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, [slug]);

  async function toggleMembership() {
    if (!slug || !community || busy) return;
    setBusy(true);
    try {
      if (community.is_member) {
        const res = await api.delete<JoinLeaveResponse>(
          `/api/v1/communities/${slug}/leave`
        );
        setCommunity({
          ...community,
          is_member: res.is_member,
          member_count: res.member_count,
        });
      } else {
        const res = await api.post<JoinLeaveResponse>(
          `/api/v1/communities/${slug}/join`
        );
        setCommunity({
          ...community,
          is_member: res.is_member,
          member_count: res.member_count,
        });
      }
    } catch (err) {
      const msg =
        err instanceof ApiError
          ? typeof err.detail === "string"
            ? err.detail
            : "Action failed"
          : "Action failed";
      alert(msg);
    } finally {
      setBusy(false);
    }
  }

  if (loading) {
    return <div className="p-8 text-center text-gray-400">Loading...</div>;
  }

  if (error || !community) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-6">
        <div className="bg-red-50 border border-red-100 text-red-700 rounded-xl p-4 text-sm">
          {error ?? "Community not found"}
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto px-4 py-6">
      <Link
        to="/communities"
        className="text-sm text-gray-500 hover:text-gray-700 mb-4 inline-block"
      >
        ← All communities
      </Link>

      {/* Header */}
      <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6 mb-5">
        <div className="flex items-start gap-4">
          <span className="text-5xl">{community.emoji || "🌐"}</span>
          <div className="flex-1">
            <div className="flex items-center gap-2 flex-wrap mb-1">
              <h1 className="text-2xl font-bold text-gray-900">
                {community.name}
              </h1>
              {community.is_moderator && (
                <span className="text-[10px] uppercase tracking-wider px-2 py-0.5 rounded-full bg-sky-50 text-sky-700 border border-sky-200">
                  you moderate
                </span>
              )}
              {!community.is_public && (
                <span className="text-[10px] uppercase tracking-wider px-2 py-0.5 rounded-full bg-gray-50 text-gray-600 border border-gray-200">
                  private
                </span>
              )}
            </div>
            <p className="text-sm text-gray-500">c/{community.slug}</p>
            <div className="flex items-center gap-3 mt-2 text-xs text-gray-500">
              <span>#{community.interest_slug}</span>
              <span>
                <strong className="text-gray-900">{community.member_count}</strong>{" "}
                {community.member_count === 1 ? "member" : "members"}
              </span>
            </div>
          </div>
        </div>

        {community.description && (
          <p className="text-sm text-gray-700 mt-4 leading-relaxed">
            {community.description}
          </p>
        )}

        {/* Actions */}
        <div className="mt-4 flex items-center gap-3 flex-wrap">
          <button
            onClick={toggleMembership}
            disabled={busy}
            className={`text-sm px-4 py-2 rounded-lg transition-colors press ${
              community.is_member
                ? "border border-gray-300 text-gray-700 hover:bg-gray-50"
                : "bg-sky-600 text-white hover:bg-sky-700"
            } disabled:opacity-50`}
          >
            {busy
              ? "..."
              : community.is_member
              ? "Leave community"
              : "Join community"}
          </button>

          {community.is_member && (
            <Link
              to={`/post/new?community=${community.id}`}
              className="text-sm px-4 py-2 bg-sky-600 text-white rounded-lg hover:bg-sky-700 transition-colors press"
            >
              + Post in this community
            </Link>
          )}

          {community.is_moderator && (
            <span className="text-xs text-gray-500">
              You're the moderator of this community.
            </span>
          )}
        </div>
      </div>

      {/* Posts */}
      <h2 className="text-lg font-semibold text-gray-900 mb-3">
        Posts in this community
      </h2>
      {posts.length === 0 ? (
        <div className="text-center py-16 text-gray-400">
          <p className="text-4xl mb-2">📝</p>
          <p className="text-sm">No posts here yet.</p>
          <p className="text-xs mt-2">
            {community.is_member
              ? "Be the first — click “Post in this community” above."
              : "Join this community to start posting."}
          </p>
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