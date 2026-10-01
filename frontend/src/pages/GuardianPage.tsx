import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import { api, ApiError } from "../lib/api";

interface Child {
  id: string;
  email: string;
  username: string;
  display_name: string | null;
  is_child_account: boolean;
  is_active: boolean;
  created_at: string;
}

interface ChildActivity {
  child_id: string;
  post_count: number;
  recent_posts: {
    id: string;
    text: string;
    interest_slug: string;
    moderation_status: string;
    created_at: string;
  }[];
}

export default function GuardianPage() {
  const [children, setChildren] = useState<Child[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreate, setShowCreate] = useState(false);

  // Create child form
  const [email, setEmail] = useState("");
  const [username, setUsername] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [password, setPassword] = useState("");
  const [creating, setCreating] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);

  // Activity viewer
  const [activeChild, setActiveChild] = useState<Child | null>(null);
  const [activity, setActivity] = useState<ChildActivity | null>(null);
  const [activityLoading, setActivityLoading] = useState(false);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const list = await api.get<Child[]>("/api/v1/guardian/children");
      setChildren(list);
    } catch (err) {
      setError(
        err instanceof ApiError
          ? typeof err.detail === "string"
            ? err.detail
            : "Failed to load children"
          : "Failed to load children"
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function handleCreate(e: FormEvent) {
    e.preventDefault();
    setCreateError(null);
    if (password.length < 8) {
      setCreateError("Password must be at least 8 characters");
      return;
    }
    setCreating(true);
    try {
      await api.post("/api/v1/guardian/children", {
        email,
        username,
        display_name: displayName || username,
        password,
      });
      setShowCreate(false);
      setEmail("");
      setUsername("");
      setDisplayName("");
      setPassword("");
      await load();
    } catch (err) {
      const msg =
        err instanceof ApiError
          ? typeof err.detail === "string"
            ? err.detail
            : "Failed to create child account"
          : "Failed to create child account";
      setCreateError(msg);
    } finally {
      setCreating(false);
    }
  }

  async function viewActivity(child: Child) {
    setActiveChild(child);
    setActivity(null);
    setActivityLoading(true);
    try {
      const a = await api.get<ChildActivity>(
        `/api/v1/guardian/children/${child.id}/activity`
      );
      setActivity(a);
    } catch {
      setActivity(null);
    } finally {
      setActivityLoading(false);
    }
  }

  return (
    <div className="max-w-3xl mx-auto px-4 py-6">
      <div className="flex items-center justify-between mb-2">
        <h1 className="text-2xl font-bold text-gray-900">Guardian controls</h1>
        <button
          onClick={() => setShowCreate((s) => !s)}
          className="text-sm px-3 py-1.5 bg-sky-600 text-white rounded-lg hover:bg-sky-700"
        >
          {showCreate ? "Cancel" : "+ Create child account"}
        </button>
      </div>
      <p className="text-sm text-gray-500 mb-6">
        Create and manage accounts for children. Child accounts are
        automatically placed into Kids focus mode and restricted from
        unapproved content.
      </p>

      {showCreate && (
        <form
          onSubmit={handleCreate}
          className="bg-white border border-gray-200 rounded-2xl p-5 mb-6"
        >
          <h2 className="font-semibold text-gray-900 mb-4">New child account</h2>

          <input
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            type="email"
            placeholder="Child's email"
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm mb-3 focus:outline-none focus:ring-2 focus:ring-sky-500"
            required
          />
          <input
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            placeholder="Username"
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm mb-3 focus:outline-none focus:ring-2 focus:ring-sky-500"
            required
            minLength={3}
          />
          <input
            value={displayName}
            onChange={(e) => setDisplayName(e.target.value)}
            placeholder="Display name (optional)"
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm mb-3 focus:outline-none focus:ring-2 focus:ring-sky-500"
          />
          <input
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            type="password"
            placeholder="Password (at least 8 characters)"
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm mb-3 focus:outline-none focus:ring-2 focus:ring-sky-500"
            required
            minLength={8}
          />

          {createError && (
            <div className="text-sm text-red-600 bg-red-50 border border-red-100 rounded-lg px-3 py-2 mb-3">
              {createError}
            </div>
          )}

          <button
            type="submit"
            disabled={creating}
            className="w-full py-2 bg-sky-600 text-white text-sm rounded-lg hover:bg-sky-700 disabled:opacity-50"
          >
            {creating ? "Creating..." : "Create child account"}
          </button>
        </form>
      )}

      {loading && (
        <div className="text-center py-12 text-gray-400">Loading...</div>
      )}
      {error && (
        <div className="bg-red-50 border border-red-100 text-red-700 rounded-xl p-4 text-sm">
          {error}
        </div>
      )}

      {!loading && !error && children.length === 0 && (
        <div className="text-center py-16 text-gray-400">
          <p className="text-4xl mb-3">🧸</p>
          <p>No child accounts yet.</p>
          <p className="text-xs mt-2">Create one to get started.</p>
        </div>
      )}

      {!loading && !error && children.length > 0 && (
        <div className="space-y-3">
          {children.map((child) => (
            <div
              key={child.id}
              className="bg-white rounded-2xl border border-gray-100 shadow-sm p-5"
            >
              <div className="flex items-start justify-between gap-3">
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="font-semibold text-gray-900">
                      {child.display_name || child.username}
                    </h3>
                    <span className="text-xs px-2 py-0.5 rounded-full bg-green-50 text-green-700 border border-green-100">
                      child-safe
                    </span>
                  </div>
                  <p className="text-sm text-gray-500">@{child.username}</p>
                  <p className="text-xs text-gray-400 mt-1">{child.email}</p>
                </div>
                <button
                  onClick={() => viewActivity(child)}
                  className="text-xs px-3 py-1.5 bg-sky-600 text-white rounded-lg hover:bg-sky-700"
                >
                  View activity
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Activity modal/panel */}
      {activeChild && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center p-4 z-50 animate-fade-in">
            <div className="bg-white rounded-2xl max-w-lg w-full max-h-[80vh] overflow-y-auto p-5 animate-slide-up">
            <div className="flex items-center justify-between mb-4">
              <h2 className="font-semibold text-gray-900">
                Activity: @{activeChild.username}
              </h2>
              <button
                onClick={() => {
                  setActiveChild(null);
                  setActivity(null);
                }}
                className="text-gray-400 hover:text-gray-700"
              >
                ✕
              </button>
            </div>

            {activityLoading && (
              <p className="text-center py-8 text-gray-400">Loading...</p>
            )}

            {activity && (
              <>
                <div className="grid grid-cols-2 gap-4 mb-4">
                  <div className="text-center bg-gray-50 rounded-xl py-3">
                    <p className="text-2xl font-bold text-gray-900">
                      {activity.post_count}
                    </p>
                    <p className="text-xs text-gray-500">Total posts</p>
                  </div>
                  <div className="text-center bg-gray-50 rounded-xl py-3">
                    <p className="text-2xl font-bold text-gray-900">
                      {
                        activity.recent_posts.filter(
                          (p) => p.moderation_status === "approved"
                        ).length
                      }
                    </p>
                    <p className="text-xs text-gray-500">Approved</p>
                  </div>
                </div>

                {activity.recent_posts.length === 0 ? (
                  <p className="text-sm text-gray-400 text-center py-6">
                    No posts yet.
                  </p>
                ) : (
                  <div className="space-y-2">
                    {activity.recent_posts.map((p) => (
                      <div
                        key={p.id}
                        className="border border-gray-100 rounded-xl p-3"
                      >
                        <div className="flex items-center gap-2 mb-1">
                          <span className="text-xs px-2 py-0.5 rounded-full bg-gray-100 text-gray-600">
                            #{p.interest_slug}
                          </span>
                          <span
                            className={`text-xs px-2 py-0.5 rounded-full ${
                              p.moderation_status === "approved"
                                ? "bg-green-50 text-green-700"
                                : "bg-amber-50 text-amber-700"
                            }`}
                          >
                            {p.moderation_status}
                          </span>
                        </div>
                        <p className="text-sm text-gray-700 line-clamp-2">
                          {p.text}
                        </p>
                      </div>
                    ))}
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}