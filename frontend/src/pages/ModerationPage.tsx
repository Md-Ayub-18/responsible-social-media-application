import { useEffect, useState } from "react";
import { api, ApiError } from "../lib/api";
import type { Post } from "../lib/types";

interface DashboardCounts {
  pending_reports: number;
  flagged_posts: number;
  removed_posts: number;
  suspicious_accounts: number;
  pending_contributions: number;
  open_stitch_projects: number;
  total_users: number;
  total_posts: number;
}

interface DashboardResponse {
  counts: DashboardCounts;
  activity_24h: { posts: number; reports: number };
  recent_actions: {
    action: string;
    actor: string;
    target: string;
    reason: string | null;
    at: string;
  }[];
  generated_at: string;
}

interface Report {
  id: string;
  reporter_id: string;
  target_type: string;
  target_id: string;
  category: string;
  description: string | null;
  status: string;
  resolution_note: string | null;
  created_at: string;
}

interface BotSignal {
  id: string;
  user_id: string;
  score: number;
  verdict: string;
  reasons: string[];
  details: Record<string, unknown>;
  last_evaluated_at: string | null;
  username?: string | null;
  display_name?: string | null;
}

interface AuditEntry {
  id: string;
  action: string;
  actor_username: string;
  target_type: string;
  target_id: string;
  reason: string | null;
  details: Record<string, unknown>;
  created_at: string;
}

type Tab = "flagged" | "reports" | "bots" | "audit";

function timeAgo(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const sec = Math.floor(diff / 1000);
  if (sec < 60) return `${sec}s ago`;
  const min = Math.floor(sec / 60);
  if (min < 60) return `${min}m ago`;
  const hr = Math.floor(min / 60);
  if (hr < 24) return `${hr}h ago`;
  return `${Math.floor(hr / 24)}d ago`;
}

export default function ModerationPage() {
  const [tab, setTab] = useState<Tab>("flagged");
  const [dashboard, setDashboard] = useState<DashboardResponse | null>(null);
  const [flagged, setFlagged] = useState<Post[]>([]);
  const [reports, setReports] = useState<Report[]>([]);
  const [bots, setBots] = useState<BotSignal[]>([]);
  const [audit, setAudit] = useState<AuditEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);

  async function loadAll() {
    setLoading(true);
    setError(null);
    try {
      const [dash, f, r, b, a] = await Promise.all([
        api.get<DashboardResponse>("/api/v1/admin/dashboard"),
        api.get<Post[]>("/api/v1/moderation/queue?status=flagged"),
        api.get<Report[]>("/api/v1/reports/queue?status=open"),
        api.get<BotSignal[]>("/api/v1/moderation/bots/suspicious"),
        api.get<AuditEntry[]>("/api/v1/admin/audit-log?limit=30"),
      ]);
      setDashboard(dash);
      setFlagged(f);
      setReports(r);
      setBots(b);
      setAudit(a);
    } catch (err) {
      setError(
        err instanceof ApiError
          ? typeof err.detail === "string"
            ? err.detail
            : "Failed to load moderation data"
          : "Failed to load moderation data"
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadAll();
  }, []);

  async function moderatePost(postId: string, status: "approved" | "removed") {
    if (busyId) return;
    setBusyId(postId);
    try {
      await api.patch(`/api/v1/moderation/posts/${postId}`, {
        status,
        reason: status === "approved" ? "AI flag reviewed — approving" : "Confirmed violation — removing",
      });
      await loadAll();
    } catch (err) {
      alert("Failed to moderate post");
    } finally {
      setBusyId(null);
    }
  }

  async function resolveReport(reportId: string, status: "resolved" | "dismissed") {
    if (busyId) return;
    setBusyId(reportId);
    try {
      await api.patch(`/api/v1/reports/${reportId}`, {
        status,
        note: status === "resolved" ? "Action taken" : "No violation found",
      });
      await loadAll();
    } catch (err) {
      alert("Failed to resolve report");
    } finally {
      setBusyId(null);
    }
  }

  // --- Render helpers ---

  const counts = dashboard?.counts;

  return (
    <div className="max-w-5xl mx-auto px-4 py-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Moderation</h1>
        <p className="text-sm text-gray-500 mt-1">
          Review AI decisions, user reports, and suspicious accounts in one place.
        </p>
      </div>

      {/* Summary cards */}
      {counts && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-6">
          <SummaryCard label="Flagged posts" value={counts.flagged_posts} tone="red" />
          <SummaryCard label="Open reports" value={counts.pending_reports} tone="amber" />
          <SummaryCard label="Suspicious users" value={counts.suspicious_accounts} tone="purple" />
          <SummaryCard label="Removed" value={counts.removed_posts} tone="gray" />
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-1 mb-5 border-b border-gray-200">
        {([
          ["flagged", `Flagged (${flagged.length})`],
          ["reports", `Reports (${reports.length})`],
          ["bots", `Bots (${bots.length})`],
          ["audit", "Audit log"],
        ] as [Tab, string][]).map(([key, label]) => (
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

      {loading && (
        <div className="text-center py-12 text-gray-400">Loading...</div>
      )}
      {error && (
        <div className="bg-red-50 border border-red-100 text-red-700 rounded-xl p-4 text-sm">
          {error}
        </div>
      )}

      {/* Flagged posts */}
      {!loading && !error && tab === "flagged" && (
        <div className="space-y-3">
          {flagged.length === 0 && <Empty label="No flagged posts. Nice and clean." />}
          {flagged.map((p) => (
            <div key={p.id} className="bg-white border border-gray-100 rounded-2xl p-5 shadow-sm">
              <div className="flex items-start justify-between gap-3 mb-2">
                <div className="flex items-center gap-2">
                  <span className="text-xs px-2 py-0.5 rounded-full bg-red-50 text-red-700 border border-red-100">
                    {p.interest_slug}
                  </span>
                  <span className="text-xs text-gray-400">{timeAgo(p.created_at)}</span>
                </div>
              </div>
              <p className="text-gray-800 whitespace-pre-wrap">{p.text}</p>
              {p.moderation_reason && (
                <p className="text-xs text-red-700 bg-red-50 border border-red-100 rounded-lg px-3 py-2 mt-3">
                  ⚠️ {p.moderation_reason}
                </p>
              )}
              <div className="flex items-center justify-end gap-2 mt-4">
                <button
                  disabled={busyId === p.id}
                  onClick={() => moderatePost(p.id, "approved")}
                  className="text-xs px-3 py-1.5 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
                >
                  Approve
                </button>
                <button
                  disabled={busyId === p.id}
                  onClick={() => moderatePost(p.id, "removed")}
                  className="text-xs px-3 py-1.5 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50"
                >
                  Remove
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Reports */}
      {!loading && !error && tab === "reports" && (
        <div className="space-y-3">
          {reports.length === 0 && <Empty label="No open reports." />}
          {reports.map((r) => (
            <div key={r.id} className="bg-white border border-gray-100 rounded-2xl p-5 shadow-sm">
              <div className="flex items-start justify-between gap-3 mb-2">
                <span className="text-xs px-2 py-0.5 rounded-full bg-amber-50 text-amber-700 border border-amber-100">
                  {r.category}
                </span>
                <span className="text-xs text-gray-400">{timeAgo(r.created_at)}</span>
              </div>
              <p className="text-sm text-gray-700">
                <span className="font-medium">{r.target_type}</span> · {r.target_id.slice(0, 8)}...
              </p>
              {r.description && (
                <p className="text-sm text-gray-600 mt-2 italic">"{r.description}"</p>
              )}
              <div className="flex items-center justify-end gap-2 mt-4">
                <button
                  disabled={busyId === r.id}
                  onClick={() => resolveReport(r.id, "resolved")}
                  className="text-xs px-3 py-1.5 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
                >
                  Resolve
                </button>
                <button
                  disabled={busyId === r.id}
                  onClick={() => resolveReport(r.id, "dismissed")}
                  className="text-xs px-3 py-1.5 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 disabled:opacity-50"
                >
                  Dismiss
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Bots */}
      {!loading && !error && tab === "bots" && (
        <div className="space-y-3">
          {bots.length === 0 && <Empty label="No suspicious accounts detected." />}
          {bots.map((b) => (
            <div key={b.id} className="bg-white border border-gray-100 rounded-2xl p-5 shadow-sm">
              <div className="flex items-center justify-between gap-3 mb-2">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-semibold text-gray-900">
                    @{b.username ?? b.user_id.slice(0, 8)}
                  </span>
                  <span
                    className={`text-xs px-2 py-0.5 rounded-full ${
                      b.verdict === "confirmed_bot"
                        ? "bg-red-50 text-red-700 border border-red-100"
                        : "bg-amber-50 text-amber-700 border border-amber-100"
                    }`}
                  >
                    {b.verdict}
                  </span>
                </div>
                <span className="text-xs text-gray-400">
                  score {b.score.toFixed(2)}
                </span>
              </div>
              <ul className="text-sm text-gray-600 space-y-1">
                {b.reasons.map((r, i) => (
                  <li key={i}>• {r}</li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      )}

      {/* Audit log */}
      {!loading && !error && tab === "audit" && (
        <div className="space-y-2">
          {audit.length === 0 && <Empty label="No audit entries yet." />}
          {audit.map((a) => (
            <div
              key={a.id}
              className="bg-white border border-gray-100 rounded-xl px-4 py-3 shadow-sm flex items-start justify-between gap-3"
            >
              <div>
                <p className="text-sm text-gray-800">
                  <span className="font-medium">{a.action}</span>{" "}
                  <span className="text-gray-500">on {a.target_type}:{a.target_id.slice(0, 8)}</span>
                </p>
                {a.reason && (
                  <p className="text-xs text-gray-500 mt-1">"{a.reason}"</p>
                )}
              </div>
              <div className="text-right text-xs text-gray-400 whitespace-nowrap">
                <div>{a.actor_username}</div>
                <div>{timeAgo(a.created_at)}</div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function SummaryCard({
  label,
  value,
  tone,
}: {
  label: string;
  value: number;
  tone: "red" | "amber" | "purple" | "gray";
}) {
  const tones = {
    red: "bg-red-50 border-red-100 text-red-700",
    amber: "bg-amber-50 border-amber-100 text-amber-700",
    purple: "bg-purple-50 border-purple-100 text-purple-700",
    gray: "bg-gray-50 border-gray-100 text-gray-700",
  } as const;

  return (
    <div className={`rounded-2xl border p-4 ${tones[tone]}`}>
      <p className="text-xs font-medium uppercase tracking-wider opacity-80">
        {label}
      </p>
      <p className="text-2xl font-bold mt-1">{value}</p>
    </div>
  );
}

function Empty({ label }: { label: string }) {
  return (
    <div className="text-center py-12 text-gray-400">
      <p className="text-3xl mb-2">✓</p>
      <p className="text-sm">{label}</p>
    </div>
  );
}