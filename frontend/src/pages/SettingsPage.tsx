import { useEffect, useState } from "react";
import { useAuth } from "../contexts/AuthContext";
import TierBadge from "../components/TierBadge";
import { api, ApiError } from "../lib/api";
import type { BlockedUser, User } from "../lib/types";

export default function SettingsPage() {
  const { user, setUser } = useAuth();
  const [toggling, setToggling] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!user) return null;

  async function togglePrivacy() {
    if (!user || toggling) return;
    setToggling(true);
    setError(null);
    try {
      const updated = await api.patch<User>("/api/v1/users/me/privacy", {
        is_private: !user.is_private,
      });
      setUser(updated);
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Failed to update");
    } finally {
      setToggling(false);
    }
  }

  return (
    <div className="max-w-2xl mx-auto px-4 py-6">
      <h1 className="text-2xl font-bold text-gray-900 mb-1">Settings</h1>
      <p className="text-sm text-gray-500 mb-6">
        Manage your account and preferences.
      </p>

      {/* Profile */}
      <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6 mb-4">
        <h2 className="font-semibold text-gray-900 mb-4">Profile</h2>
        <div className="space-y-3 text-sm">
          <Row label="Username" value={`@${user.username}`} />
          <Row label="Email" value={user.email} />
          <Row
            label="Display name"
            value={user.display_name || user.username}
          />
          <div className="flex items-center justify-between">
            <span className="text-gray-500">Account tier</span>
            <TierBadge tier={user.account_tier} size="sm" />
          </div>
          <Row label="Date of birth" value={user.date_of_birth || "Not set"} />
        </div>
      </div>

      {/* Privacy */}
      <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6 mb-4">
        <h2 className="font-semibold text-gray-900 mb-1">Privacy</h2>
        <p className="text-sm text-gray-500 mb-4">
          Control who can see your posts.
        </p>

        <div className="flex items-start justify-between gap-4">
          <div className="flex-1">
            <p className="font-medium text-gray-900">
              {user.is_private ? "🔒 Private account" : "🌐 Public account"}
            </p>
            <p className="text-xs text-gray-500 mt-1 leading-relaxed">
              {user.is_private
                ? "Only your followers can see your posts in their feed."
                : "Anyone with matching interests can see your posts."}
            </p>
          </div>
          <button
            onClick={togglePrivacy}
            disabled={toggling}
            className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors flex-shrink-0 ${
              user.is_private ? "bg-sky-600" : "bg-gray-200"
            } disabled:opacity-50`}
            aria-label="Toggle private account"
          >
            <span
              className={`inline-block h-5 w-5 transform rounded-full bg-white transition-transform shadow ${
                user.is_private ? "translate-x-5" : "translate-x-0.5"
              }`}
            />
          </button>
        </div>

        {error && (
          <div className="mt-3 text-sm text-red-600 bg-red-50 border border-red-100 rounded-lg px-3 py-2">
            {error}
          </div>
        )}
      </div>

      {/* Blocked users */}
      <BlockedUsersSection />

      
      {/* Screen time */}
<div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6 mb-4">
  <h2 className="font-semibold text-gray-900 mb-1">Screen time</h2>
  <p className="text-sm text-gray-500 mb-4">
    Get a friendly nudge when you've been on Verity for a while.
  </p>

  <div className="space-y-4">
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-2">
        Daily limit: {user.daily_screen_time_limit_minutes} minutes
      </label>
      <input
        type="range"
        min={15}
        max={240}
        step={15}
        value={user.daily_screen_time_limit_minutes}
        onChange={async (e) => {
          const minutes = parseInt(e.target.value, 10);
          const updated = await api.patch<User>("/api/v1/screen-time/limit", {
            daily_screen_time_limit_minutes: minutes,
            break_reminders_enabled: user.break_reminders_enabled,
          });
          setUser(updated);
        }}
        className="w-full"
      />
    </div>

    <label className="flex items-center gap-3 text-sm text-gray-700">
      <input
        type="checkbox"
        checked={user.break_reminders_enabled}
        disabled={user.is_child_account}
        onChange={async (e) => {
          const updated = await api.patch<User>("/api/v1/screen-time/limit", {
            daily_screen_time_limit_minutes: user.daily_screen_time_limit_minutes,
            break_reminders_enabled: e.target.checked,
          });
          setUser(updated);
        }}
      />
      <span>
        Show break reminders
        {user.is_child_account && (
          <span className="text-xs text-gray-400 ml-1">
            (cannot be disabled for child accounts)
          </span>
        )}
      </span>
    </label>
  </div>
</div>

      {/* Coming soon */}
      <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
        <h2 className="font-semibold text-gray-900 mb-2">Coming soon</h2>
        <p className="text-sm text-gray-500">
          Profile pictures, avatar upload, and password change will be available
          here soon.
        </p>
      </div>
    </div>
  );
}

/* ---------- Sub-components ---------- */

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-gray-500">{label}</span>
      <span className="font-medium text-gray-900">{value}</span>
    </div>
  );
}

function BlockedUsersSection() {
  const [blocked, setBlocked] = useState<BlockedUser[]>([]);
  const [loading, setLoading] = useState(true);

  async function load() {
    try {
      const list = await api.get<BlockedUser[]>("/api/v1/blocks");
      setBlocked(list);
    } catch {
      // silent
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function unblock(username: string) {
    try {
      await api.delete(`/api/v1/blocks/${username}`);
      setBlocked((prev) => prev.filter((b) => b.username !== username));
    } catch {
      alert("Failed to unblock");
    }
  }

  return (
    <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6 mb-4">
      <h2 className="font-semibold text-gray-900 mb-3">Blocked users</h2>
      {loading ? (
        <p className="text-sm text-gray-400">Loading...</p>
      ) : blocked.length === 0 ? (
        <p className="text-sm text-gray-500">You haven't blocked anyone.</p>
      ) : (
        <ul className="space-y-2">
          {blocked.map((u) => (
            <li
              key={u.user_id}
              className="flex items-center justify-between py-2 border-b border-gray-100 last:border-0"
            >
              <span className="text-sm text-gray-800">@{u.username}</span>
              <button
                onClick={() => unblock(u.username)}
                className="text-xs px-3 py-1 border border-gray-300 rounded-lg text-gray-600 hover:bg-gray-50"
              >
                Unblock
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}