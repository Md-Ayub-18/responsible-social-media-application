import { useState } from "react";
import { api } from "../lib/api";
import type { Post } from "../lib/types";

interface PostCardProps {
  post: Post;
  onLikeChange?: (postId: string, liked: boolean, count: number) => void;
}

function timeAgo(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const sec = Math.floor(diff / 1000);
  if (sec < 60) return `${sec}s ago`;
  const min = Math.floor(sec / 60);
  if (min < 60) return `${min}m ago`;
  const hr = Math.floor(min / 60);
  if (hr < 24) return `${hr}h ago`;
  const d = Math.floor(hr / 24);
  return `${d}d ago`;
}

const INTEREST_META: Record<string, { emoji: string; color: string }> = {
  learning:      { emoji: "📚", color: "bg-blue-50 text-blue-700 border-blue-100" },
  sports:        { emoji: "⚽", color: "bg-green-50 text-green-700 border-green-100" },
  art:           { emoji: "🎨", color: "bg-pink-50 text-pink-700 border-pink-100" },
  technology:    { emoji: "💻", color: "bg-indigo-50 text-indigo-700 border-indigo-100" },
  entertainment: { emoji: "🎬", color: "bg-purple-50 text-purple-700 border-purple-100" },
  personal:      { emoji: "💬", color: "bg-yellow-50 text-yellow-700 border-yellow-100" },
  social_causes: { emoji: "🌱", color: "bg-teal-50 text-teal-700 border-teal-100" },
};

function isVideoUrl(url: string): boolean {
  return /\.(mp4|mov|webm)$/i.test(url);
}

export default function PostCard({ post, onLikeChange }: PostCardProps) {
  const meta = INTEREST_META[post.interest_slug] ?? {
    emoji: "📝",
    color: "bg-gray-50 text-gray-700 border-gray-100",
  };

  const [liked, setLiked] = useState(post.is_liked_by_me);
  const [count, setCount] = useState(post.reaction_count);
  const [busy, setBusy] = useState(false);
  const [justLiked, setJustLiked] = useState(false);

  async function toggleLike() {
    if (busy) return;
    setBusy(true);

    const wasLiked = liked;
    const nextLiked = !liked;
    const nextCount = count + (nextLiked ? 1 : -1);
    setLiked(nextLiked);
    setCount(nextCount);

    // pop animation only on like (not unlike)
    if (nextLiked) {
      setJustLiked(true);
      setTimeout(() => setJustLiked(false), 400);
    }

    try {
      const res = await api.post<{ is_liked: boolean; reaction_count: number }>(
        `/api/v1/posts/${post.id}/like`
      );
      setLiked(res.is_liked);
      setCount(res.reaction_count);
      onLikeChange?.(post.id, res.is_liked, res.reaction_count);
    } catch {
      // revert
      setLiked(wasLiked);
      setCount(count);
    } finally {
      setBusy(false);
    }
  }

  return (
    <article className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden hover-lift animate-fade-in-up">
      {/* Header row */}
      <div className="flex items-center justify-between px-5 pt-4">
        <span
          className={`inline-flex items-center gap-1.5 text-xs font-medium px-2.5 py-1 rounded-full border ${meta.color}`}
        >
          <span>{meta.emoji}</span>
          <span>{post.interest_slug.replace("_", " ")}</span>
        </span>
        <span className="text-xs text-gray-400">{timeAgo(post.created_at)}</span>
      </div>

      {/* Media (if any) */}
     {post.media_urls.length > 0 && (
  <>
    {post.media_moderation_status === "flagged" ? (
      <div className="mt-3 mx-5 rounded-xl border-2 border-dashed border-red-200 bg-red-50 px-4 py-8 text-center">
        <div className="text-4xl mb-2">🚩</div>
        <p className="text-sm font-medium text-red-700">
          Image hidden — flagged by automated moderation
        </p>
        <p className="text-xs text-red-600 mt-1">
          Reviewers will look at this. You can still see your own post.
        </p>
      </div>
    ) : (
      <div className="mt-3 bg-black flex items-center justify-center">
        {isVideoUrl(post.media_urls[0]) ? (
          <video
            src={post.media_urls[0]}
            controls
            className="w-full max-h-[600px] bg-black"
          />
        ) : (
          <img
            src={post.media_urls[0]}
            alt=""
            className="w-full max-h-[600px] object-contain"
          />
        )}
      </div>
    )}
  </>
)}

      <div className="px-5 py-4">
        {/* Text */}
        <p className="text-gray-800 leading-relaxed whitespace-pre-wrap">
          {post.text}
        </p>

        {/* Badges + Like row */}
        <div className="flex items-center justify-between mt-4">
          <div className="flex flex-wrap gap-2">
            {post.audience === "private" && (
  <span className="inline-flex items-center gap-1 text-xs px-2 py-1 rounded-md bg-gray-100 text-gray-600 border border-gray-200">
    🔒 Followers only
  </span>
)}
            {post.ai_label_shown && (
              <span className="inline-flex items-center gap-1 text-xs px-2 py-1 rounded-md bg-amber-50 text-amber-700 border border-amber-100">
                ✨ AI-generated
              </span>
            )}
            {post.media_urls.length > 0 && post.media_moderation_status === "pending" && (
  <span className="inline-flex items-center gap-1 text-xs px-2 py-1 rounded-md bg-gray-50 text-gray-600 border border-gray-100">
    ⏳ Checking media...
  </span>
)}
            {post.moderation_status === "flagged" && (
              <span
                className="inline-flex items-center gap-1 text-xs px-2 py-1 rounded-md bg-red-50 text-red-700 border border-red-100"
                title={post.moderation_reason ?? undefined}
              >
                🚩 Under review
              </span>
            )}
            {post.moderation_status === "removed" && (
              <span className="inline-flex items-center gap-1 text-xs px-2 py-1 rounded-md bg-gray-100 text-gray-500 border border-gray-200">
                🚫 Removed
              </span>
            )}
          </div>

          {/* Like button */}
          <button
            onClick={toggleLike}
            disabled={busy}
            className={`flex items-center gap-1.5 text-sm px-3 py-1.5 rounded-full transition-all press ${
              liked
                ? "bg-red-50 text-red-600 border border-red-100"
                : "text-gray-500 hover:bg-gray-50 border border-transparent"
            } ${justLiked ? "animate-pop" : ""}`}
          >
            <span>{liked ? "❤️" : "🤍"}</span>
            <span className="text-xs font-medium">{count}</span>
          </button>
        </div>
      </div>
    </article>
  );
}