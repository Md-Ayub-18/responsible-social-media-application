import { Link } from "react-router-dom";
import type { Community } from "../lib/types";

const INTEREST_META: Record<string, { emoji: string; color: string }> = {
  learning:      { emoji: "📚", color: "bg-blue-50 text-blue-700 border-blue-200" },
  sports:        { emoji: "⚽", color: "bg-green-50 text-green-700 border-green-200" },
  art:           { emoji: "🎨", color: "bg-pink-50 text-pink-700 border-pink-200" },
  technology:    { emoji: "💻", color: "bg-indigo-50 text-indigo-700 border-indigo-200" },
  entertainment: { emoji: "🎬", color: "bg-purple-50 text-purple-700 border-purple-200" },
  personal:      { emoji: "💬", color: "bg-yellow-50 text-yellow-700 border-yellow-200" },
  social_causes: { emoji: "🌱", color: "bg-teal-50 text-teal-700 border-teal-200" },
};

export default function CommunityCard({ community }: { community: Community }) {
  const meta = INTEREST_META[community.interest_slug] ?? {
    emoji: "📝",
    color: "bg-gray-50 text-gray-700 border-gray-200",
  };

  return (
    <Link
      to={`/c/${community.slug}`}
      className="block bg-white rounded-2xl border border-gray-100 shadow-sm p-5 hover:border-gray-300 hover-lift transition-all"
    >
      <div className="flex items-start gap-3">
        <span className="text-3xl">{community.emoji || meta.emoji}</span>
        <div className="flex-1">
          <div className="flex items-center gap-2 flex-wrap">
            <h3 className="font-semibold text-gray-900">{community.name}</h3>
            <span
              className={`text-[10px] px-2 py-0.5 rounded-full border ${meta.color}`}
            >
              {community.interest_slug}
            </span>
            {community.is_moderator && (
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-sky-50 text-sky-700 border border-sky-200">
                you moderate
              </span>
            )}
            {!community.is_public && (
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-gray-50 text-gray-600 border border-gray-200">
                private
              </span>
            )}
          </div>

          {community.description && (
            <p className="text-sm text-gray-600 mt-1 line-clamp-2">
              {community.description}
            </p>
          )}

          <div className="flex items-center gap-3 mt-2 text-xs text-gray-400">
            <span>
              <strong className="text-gray-600">{community.member_count}</strong>{" "}
              {community.member_count === 1 ? "member" : "members"}
            </span>
            {community.is_member && (
              <span className="text-sky-600 font-medium">✓ Joined</span>
            )}
          </div>
        </div>
      </div>
    </Link>
  );
}