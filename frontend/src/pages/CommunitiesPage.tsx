import { useEffect, useState } from "react";
import { api, ApiError } from "../lib/api";
import type { Community, CommunityListResponse, Interest } from "../lib/types";
import CommunityCard from "../components/CommunityCard";
import CreateCommunityForm from "../components/CreateCommunityForm";

export default function CommunitiesPage() {
  const [communities, setCommunities] = useState<Community[]>([]);
  const [interests, setInterests] = useState<Interest[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tab, setTab] = useState<"all" | "mine">("all");
  const [showCreate, setShowCreate] = useState(false);
  const [query, setQuery] = useState("");

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const [all, ints] = await Promise.all([
        api.get<CommunityListResponse>("/api/v1/communities"),
        api.get<Interest[]>("/api/v1/interests/"),
      ]);
      setCommunities(all.communities);
      setInterests(ints);
    } catch (err) {
      setError(
        err instanceof ApiError
          ? typeof err.detail === "string"
            ? err.detail
            : "Failed to load communities"
          : "Failed to load communities"
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  // Compute the visible list
  const baseList = tab === "mine"
    ? communities.filter((c) => c.is_member)
    : communities;

  const filtered = query.trim()
    ? baseList.filter((c) => {
        const q = query.toLowerCase().trim();
        return (
          c.name.toLowerCase().includes(q) ||
          (c.description ?? "").toLowerCase().includes(q) ||
          c.interest_slug.toLowerCase().includes(q) ||
          c.slug.toLowerCase().includes(q)
        );
      })
    : baseList;

  const myCount = communities.filter((c) => c.is_member).length;

  return (
    <div className="max-w-3xl mx-auto px-4 py-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-2">
        <h1 className="text-2xl font-bold text-gray-900">Communities</h1>
        <button
          onClick={() => setShowCreate((s) => !s)}
          className="text-sm px-3 py-1.5 bg-sky-600 text-white rounded-lg hover:bg-sky-700 transition-colors press"
        >
          {showCreate ? "Close" : "+ New community"}
        </button>
      </div>
      <p className="text-sm text-gray-500 mb-6">
        Interest-based spaces where people gather, post, and discuss around a shared topic.
      </p>

      {/* Create form (extracted) */}
      {showCreate && (
        <CreateCommunityForm
          interests={interests}
          onCancel={() => setShowCreate(false)}
          onCreated={() => setShowCreate(false)}
        />
      )}

      {/* Search */}
      <div className="relative mb-4">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search communities by name, topic, or description..."
          className="w-full pl-10 pr-10 py-2.5 text-sm border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-sky-500 focus:border-transparent"
        />
        <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none">
          🔍
        </span>
        {query && (
          <button
            onClick={() => setQuery("")}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-700 text-lg leading-none"
            aria-label="Clear search"
          >
            ×
          </button>
        )}
      </div>

      {/* Tabs */}
      <div className="flex gap-1 mb-5 border-b border-gray-200">
        {(
          [
            ["all", `All (${communities.length})`],
            ["mine", `My communities (${myCount})`],
          ] as const
        ).map(([key, label]) => (
          <button
            key={key}
            onClick={() => setTab(key)}
            className={`px-4 py-2.5 text-sm font-medium border-b-2 transition-colors ${
              tab === key
                ? "border-sky-600 text-sky-700"
                : "border-transparent text-gray-500 hover:text-gray-700"
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      {/* Results */}
      {loading && (
        <div className="text-center py-12 text-gray-400">Loading...</div>
      )}

      {error && (
        <div className="bg-red-50 border border-red-100 text-red-700 rounded-xl p-4 text-sm">
          {error}
        </div>
      )}

      {!loading && !error && filtered.length === 0 && (
        <EmptyState
          query={query}
          tab={tab}
          onClear={() => setQuery("")}
        />
      )}

      {!loading && !error && filtered.length > 0 && (
        <div className="space-y-3">
          {filtered.map((c) => (
            <CommunityCard key={c.id} community={c} />
          ))}
        </div>
      )}

      {/* Result count */}
      {query && !loading && !error && (
        <p className="text-xs text-gray-400 mt-4 text-center">
          {filtered.length} {filtered.length === 1 ? "result" : "results"} for "{query}"
        </p>
      )}
    </div>
  );
}

/* ---------- Empty state ---------- */

function EmptyState({
  query,
  tab,
  onClear,
}: {
  query: string;
  tab: "all" | "mine";
  onClear: () => void;
}) {
  if (query) {
    return (
      <div className="text-center py-16 text-gray-400">
        <p className="text-4xl mb-3">🔍</p>
        <p>No communities match "{query}"</p>
        <button
          onClick={onClear}
          className="text-xs mt-2 text-sky-600 hover:underline"
        >
          Clear search
        </button>
      </div>
    );
  }

  return (
    <div className="text-center py-16 text-gray-400">
      <p className="text-4xl mb-3">👥</p>
      <p>
        {tab === "mine"
          ? "You haven't joined any communities yet."
          : "No communities yet."}
      </p>
      <p className="text-xs mt-2">Create one to get started.</p>
    </div>
  );
}