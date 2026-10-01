import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import { api, ApiError } from "../lib/api";
import type { FocusMode, Interest } from "../lib/types";

interface ListResponse {
  modes: FocusMode[];
  count: number;
}

interface ActiveResponse {
  active_mode: FocusMode | null;
  is_active: boolean;
}

export default function FocusModesPage() {
  const [modes, setModes] = useState<FocusMode[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);

  // Create form
  const [showCreate, setShowCreate] = useState(false);
  const [allInterests, setAllInterests] = useState<Interest[]>([]);
  const [newName, setNewName] = useState("");
  const [newEmoji, setNewEmoji] = useState("🎯");
  const [newDescription, setNewDescription] = useState("");
  const [newSlugs, setNewSlugs] = useState<Set<string>>(new Set());
  const [creating, setCreating] = useState(false);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const [modesRes, activeRes, interestsRes] = await Promise.all([
        api.get<ListResponse>("/api/v1/users/me/focus-modes"),
        api.get<ActiveResponse>("/api/v1/users/me/focus-modes/active"),
        api.get<Interest[]>("/api/v1/interests/"),
      ]);
      setModes(modesRes.modes);
      setActiveId(activeRes.active_mode?.id ?? null);
      setAllInterests(interestsRes);
    } catch (err) {
      setError(
        err instanceof ApiError
          ? typeof err.detail === "string"
            ? err.detail
            : "Failed to load focus modes"
          : "Failed to load focus modes"
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function activate(modeId: string | null) {
    if (busyId) return;
    setBusyId(modeId ?? "none");
    try {
      await api.patch<ActiveResponse>("/api/v1/users/me/focus-modes/active", {
        focus_mode_id: modeId,
      });
      setActiveId(modeId);
    } catch (err) {
      console.error(err);
    } finally {
      setBusyId(null);
    }
  }

  async function deleteMode(modeId: string) {
    if (!confirm("Delete this focus mode?")) return;
    if (busyId) return;
    setBusyId(modeId);
    try {
      await api.delete(`/api/v1/users/me/focus-modes/${modeId}`);
      await load();
    } catch (err) {
      const msg =
        err instanceof ApiError
          ? typeof err.detail === "string"
            ? err.detail
            : "Cannot delete this mode"
          : "Cannot delete this mode";
      alert(msg);
    } finally {
      setBusyId(null);
    }
  }

  async function handleCreate(e: FormEvent) {
    e.preventDefault();
    if (!newName.trim()) return;
    setCreating(true);
    try {
      await api.post("/api/v1/users/me/focus-modes", {
        name: newName.trim(),
        emoji: newEmoji || null,
        description: newDescription.trim() || null,
        interest_slugs: Array.from(newSlugs),
        is_default: false,
      });
      setShowCreate(false);
      setNewName("");
      setNewEmoji("🎯");
      setNewDescription("");
      setNewSlugs(new Set());
      await load();
    } catch (err) {
      const msg =
        err instanceof ApiError
          ? typeof err.detail === "string"
            ? err.detail
            : "Failed to create focus mode"
          : "Failed to create focus mode";
      alert(msg);
    } finally {
      setCreating(false);
    }
  }

  function toggleNewSlug(slug: string) {
    setNewSlugs((prev) => {
      const next = new Set(prev);
      if (next.has(slug)) next.delete(slug);
      else next.add(slug);
      return next;
    });
  }

  return (
    <div className="max-w-3xl mx-auto px-4 py-6">
      <div className="flex items-center justify-between mb-2">
        <h1 className="text-2xl font-bold text-gray-900">Focus Modes</h1>
        <button
          onClick={() => setShowCreate((s) => !s)}
          className="text-sm px-3 py-1.5 bg-sky-600 text-white rounded-lg hover:bg-sky-700"
        >
          {showCreate ? "Cancel" : "+ New mode"}
        </button>
      </div>
      <p className="text-sm text-gray-500 mb-6">
        Modes let you switch what you see without losing your interests.
        Activate one to focus; leave none active to see everything.
      </p>

      {/* Active state + clear */}
      {activeId && (
        <div className="mb-5 flex items-center justify-between bg-sky-50 border border-sky-100 rounded-xl p-3">
          <span className="text-sm text-sky-900">
            A focus mode is active — feed is filtered.
          </span>
          <button
            onClick={() => activate(null)}
            disabled={busyId !== null}
            className="text-xs text-sky-700 hover:underline"
          >
            Turn off
          </button>
        </div>
      )}

      {/* Create form */}
      {showCreate && (
        <form
          onSubmit={handleCreate}
          className="bg-white border border-gray-200 rounded-2xl p-5 mb-6"
        >
          <h2 className="font-semibold text-gray-900 mb-4">New focus mode</h2>

          <div className="flex gap-3 mb-3">
            <input
              value={newEmoji}
              onChange={(e) => setNewEmoji(e.target.value)}
              maxLength={2}
              className="w-14 text-center text-xl border border-gray-300 rounded-lg px-2 py-2"
            />
            <input
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              placeholder="Mode name (e.g., Deep Work)"
              className="flex-1 border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-sky-500"
              required
            />
          </div>

          <input
            value={newDescription}
            onChange={(e) => setNewDescription(e.target.value)}
            placeholder="Optional description"
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm mb-4 focus:outline-none focus:ring-2 focus:ring-sky-500"
          />

          <p className="text-xs font-medium text-gray-600 mb-2">
            Interests in this mode:
          </p>
          <div className="flex flex-wrap gap-2 mb-4">
            {allInterests.map((i) => {
              const on = newSlugs.has(i.slug);
              return (
                <button
                  type="button"
                  key={i.id}
                  onClick={() => toggleNewSlug(i.slug)}
                  className={`text-xs px-3 py-1 rounded-full border transition-colors ${
                    on
                      ? "bg-sky-100 border-sky-300 text-sky-800"
                      : "bg-white border-gray-200 text-gray-600 hover:border-gray-300"
                  }`}
                >
                  {i.emoji} {i.name}
                </button>
              );
            })}
          </div>

          <button
            type="submit"
            disabled={creating || !newName.trim()}
            className="w-full py-2 bg-sky-600 text-white text-sm rounded-lg hover:bg-sky-700 disabled:opacity-50"
          >
            {creating ? "Creating..." : "Create mode"}
          </button>
        </form>
      )}

      {/* Modes list */}
      {loading && (
        <div className="text-center py-12 text-gray-400">Loading...</div>
      )}
      {error && (
        <div className="bg-red-50 border border-red-100 text-red-700 rounded-xl p-4 text-sm">
          {error}
        </div>
      )}

      {!loading && !error && (
        <div className="space-y-3">
          {modes.map((mode) => {
            const isActive = mode.id === activeId;
            const isBusy = busyId === mode.id;
            return (
              <div
                key={mode.id}
                className={`bg-white rounded-2xl border p-5 transition-all ${
                  isActive
                    ? "border-sky-500 ring-2 ring-sky-100"
                    : "border-gray-200"
                }`}
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="text-2xl">{mode.emoji}</span>
                      <h3 className="font-semibold text-gray-900">
                        {mode.name}
                      </h3>
                      {mode.is_default && (
                        <span className="text-[10px] uppercase tracking-wider text-gray-400 border border-gray-200 px-1.5 py-0.5 rounded">
                          default
                        </span>
                      )}
                      {mode.is_child_safe && (
                        <span className="text-[10px] uppercase tracking-wider text-green-700 bg-green-50 px-1.5 py-0.5 rounded">
                          child-safe
                        </span>
                      )}
                      {isActive && (
                        <span className="text-[10px] uppercase tracking-wider text-sky-700 bg-sky-50 px-1.5 py-0.5 rounded">
                          active
                        </span>
                      )}
                    </div>
                    {mode.description && (
                      <p className="text-sm text-gray-500 mt-2">
                        {mode.description}
                      </p>
                    )}
                    <div className="flex flex-wrap gap-1.5 mt-3">
                      {mode.interest_slugs.map((slug) => (
                        <span
                          key={slug}
                          className="text-xs px-2 py-0.5 rounded-full bg-gray-100 text-gray-600"
                        >
                          {slug}
                        </span>
                      ))}
                    </div>
                  </div>

                  <div className="flex flex-col gap-2">
                    {isActive ? (
                      <button
                        onClick={() => activate(null)}
                        disabled={busyId !== null}
                        className="text-xs px-3 py-1.5 border border-gray-300 rounded-lg text-gray-600 hover:bg-gray-50"
                      >
                        Deactivate
                      </button>
                    ) : (
                      <button
                        onClick={() => activate(mode.id)}
                        disabled={busyId !== null}
                        className="text-xs px-3 py-1.5 bg-sky-600 text-white rounded-lg hover:bg-sky-700 disabled:opacity-50"
                      >
                        {isBusy ? "..." : "Activate"}
                      </button>
                    )}
                    {!mode.is_default && (
                      <button
                        onClick={() => deleteMode(mode.id)}
                        disabled={busyId !== null}
                        className="text-xs px-3 py-1.5 border border-red-200 text-red-600 rounded-lg hover:bg-red-50"
                      >
                        Delete
                      </button>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      <p className="text-xs text-gray-400 mt-6 text-center">
        Changes apply instantly to your feed.
      </p>
    </div>
  );
}