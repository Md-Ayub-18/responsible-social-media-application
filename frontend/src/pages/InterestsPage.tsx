import { useEffect, useState } from "react";
import { api, ApiError } from "../lib/api";
import type { Interest } from "../lib/types";
import { Link } from "react-router-dom";

interface UserInterestsResponse {
  interests: Interest[];
  count: number;
}

export default function InterestsPage() {
  const [all, setAll] = useState<Interest[]>([]);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState<string | null>(null); // slug currently toggling

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setLoading(true);
      try {
        const [allRes, mineRes] = await Promise.all([
          api.get<Interest[]>("/api/v1/interests/"),
          api.get<UserInterestsResponse>("/api/v1/users/me/interests"),
        ]);
        if (cancelled) return;
        setAll(allRes);
        setSelected(new Set(mineRes.interests.map((i) => i.slug)));
      } catch (err) {
        if (!cancelled) {
          setError(
            err instanceof ApiError
              ? typeof err.detail === "string"
                ? err.detail
                : "Failed to load interests"
              : "Failed to load interests"
          );
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

  async function toggle(slug: string, interestId: string) {
    if (busy) return;
    setBusy(slug);
    const isSelected = selected.has(slug);
    try {
      if (isSelected) {
        await api.delete(`/api/v1/users/me/interests/${interestId}`);
        setSelected((prev) => {
          const next = new Set(prev);
          next.delete(slug);
          return next;
        });
      } else {
        await api.post("/api/v1/users/me/interests", { slug });
        setSelected((prev) => new Set(prev).add(slug));
      }
    } catch (err) {
      console.error(err);
    } finally {
      setBusy(null);
    }
  }

  return (
    <div className="max-w-3xl mx-auto px-4 py-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Interests</h1>
        <p className="text-sm text-gray-500 mt-1">
          Choose what you want to see in your feed. You can change this anytime.
        </p>
      </div>

      {loading && (
        <div className="text-center py-12 text-gray-400">Loading...</div>
      )}

      {error && (
        <div className="bg-red-50 border border-red-100 text-red-700 rounded-xl p-4 text-sm">
          {error}
        </div>
      )}

      {!loading && !error && (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {all.map((interest) => {
            const isSelected = selected.has(interest.slug);
            const isBusy = busy === interest.slug;
            return (
              <button
                key={interest.id}
                onClick={() => toggle(interest.slug, interest.id)}
                disabled={isBusy}
                className={`text-left p-4 rounded-2xl border transition-all
                  ${
                    isSelected
                      ? "border-sky-500 bg-sky-50 ring-2 ring-sky-100"
                      : "border-gray-200 bg-white hover:border-gray-300"
                  }
                  ${isBusy ? "opacity-50 cursor-wait" : "cursor-pointer"}`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-2">
                    <span className="text-2xl">{interest.emoji}</span>
                    <span className="font-semibold text-gray-900">
                      {interest.name}
                    </span>
                  </div>
                  {isSelected && (
                    <span className="text-sky-600 text-lg">✓</span>
                  )}
                </div>
                {interest.description && (
                  <p className="text-xs text-gray-500 mt-2 leading-relaxed">
                    {interest.description}
                  </p>
                )}
              </button>
            );
          })}
        </div>
      )}

      {!loading && !error && (
        <p className="text-xs text-gray-400 mt-6 text-center">
          {selected.size} selected — changes save instantly.
        </p>
      )}
      <div className="mt-8 text-center">
  <Link
    to="/feed"
    className="inline-block px-5 py-2.5 bg-sky-600 text-white text-sm font-medium rounded-lg hover:bg-sky-700 transition-colors"
  >
    View Feed →
  </Link>
</div>
    </div>
  );
}