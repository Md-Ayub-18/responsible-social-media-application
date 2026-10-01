import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import { Link, useParams } from "react-router-dom";
import { api, ApiError } from "../lib/api";
import type { Contribution, StitchProject } from "../lib/types";

interface ProjectDetail extends StitchProject {
  contributions: Contribution[];
}

export default function StitchDetailPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const [project, setProject] = useState<ProjectDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [caption, setCaption] = useState("");
  const [consent, setConsent] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [stitching, setStitching] = useState(false);

  async function load() {
    if (!projectId) return;
    setLoading(true);
    try {
      const data = await api.get<ProjectDetail>(
        `/api/v1/stitch/projects/${projectId}`
      );
      setProject(data);
    } catch (err) {
      setError(
        err instanceof ApiError
          ? typeof err.detail === "string"
            ? err.detail
            : "Failed to load project"
          : "Failed to load project"
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, [projectId]);

  async function handleUpload(e: FormEvent) {
    e.preventDefault();
    if (!file || !consent || !projectId) return;
    setUploading(true);
    setUploadError(null);
    try {
      const fd = new FormData();
      fd.append("file", file);
      if (caption.trim()) fd.append("caption", caption.trim());
      fd.append("consent_given", "true");

      await api.post(`/api/v1/stitch/projects/${projectId}/contributions`, fd);
      setFile(null);
      setCaption("");
      setConsent(false);
      await load();
    } catch (err) {
      const msg =
        err instanceof ApiError
          ? typeof err.detail === "string"
            ? err.detail
            : "Upload failed"
          : "Upload failed";
      setUploadError(msg);
    } finally {
      setUploading(false);
    }
  }

  async function moderate(id: string, status: "approved" | "rejected") {
    try {
      await api.patch(`/api/v1/stitch/contributions/${id}`, { status });
      await load();
    } catch {
      alert("Failed to moderate");
    }
  }

  async function stitch() {
    if (!projectId) return;
    setStitching(true);
    try {
      await api.post(`/api/v1/stitch/projects/${projectId}/stitch`);
      await load();
    } catch (err) {
      const msg =
        err instanceof ApiError
          ? typeof err.detail === "string"
            ? err.detail
            : "Stitching failed"
          : "Stitching failed";
      alert(msg);
    } finally {
      setStitching(false);
    }
  }

  if (loading) return <div className="p-8 text-center text-gray-400">Loading...</div>;
  if (error || !project) {
    return (
      <div className="max-w-3xl mx-auto px-4 py-6">
        <div className="bg-red-50 border border-red-100 text-red-700 rounded-xl p-4 text-sm">
          {error ?? "Project not found"}
        </div>
      </div>
    );
  }

  const approvedCount = project.contributions.filter((c) => c.status === "approved").length;

  return (
    <div className="max-w-3xl mx-auto px-4 py-6">
      <Link to="/stitch" className="text-sm text-gray-500 hover:text-gray-700 mb-4 inline-block">
        ← All projects
      </Link>

      {/* Header */}
      <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6 mb-5">
        <div className="flex items-start justify-between gap-3 mb-2">
          <h1 className="text-2xl font-bold text-gray-900">{project.title}</h1>
          <span
            className={`text-xs px-2.5 py-1 rounded-full ${
              project.status === "stitched"
                ? "bg-green-50 text-green-700 border border-green-100"
                : project.status === "open"
                ? "bg-sky-50 text-sky-700 border border-sky-100"
                : "bg-gray-50 text-gray-600 border border-gray-100"
            }`}
          >
            {project.status}
          </span>
        </div>
        {project.description && (
          <p className="text-sm text-gray-600">{project.description}</p>
        )}
        <div className="flex items-center gap-4 mt-3 text-xs text-gray-500">
          <span>#{project.interest_slug}</span>
          <span>{project.contributions.length} contribution(s)</span>
          <span>{approvedCount} approved</span>
        </div>
      </div>

      {/* Stitched video */}
      {project.stitched_video_url && (
        <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-5 mb-5">
          <h2 className="font-semibold text-gray-900 mb-3">🎬 Final output</h2>
          <video
            controls
            src={project.stitched_video_url}
            className="w-full rounded-xl bg-black"
          />
        </div>
      )}

      {/* Contribute form */}
      {project.allow_contributions && project.status !== "stitched" && (
        <form
          onSubmit={handleUpload}
          className="bg-white rounded-2xl border border-gray-100 shadow-sm p-5 mb-5"
        >
          <h2 className="font-semibold text-gray-900 mb-3">Submit a clip</h2>
          <input
            type="file"
            accept="video/mp4,video/quicktime,video/webm"
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
            className="block w-full text-sm text-gray-600 file:mr-3 file:py-2 file:px-4 file:rounded-lg file:border-0 file:bg-sky-50 file:text-sky-700 hover:file:bg-sky-100 file:cursor-pointer mb-3"
          />
          <input
            value={caption}
            onChange={(e) => setCaption(e.target.value)}
            placeholder="Optional caption"
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm mb-3 focus:outline-none focus:ring-2 focus:ring-sky-500"
          />
          <label className="flex items-start gap-2 text-sm text-gray-700 mb-4">
            <input
              type="checkbox"
              checked={consent}
              onChange={(e) => setConsent(e.target.checked)}
              className="mt-0.5"
            />
            <span>
              I give my consent for this clip to be reviewed and used in the
              final stitched video.
            </span>
          </label>
          {uploadError && (
            <div className="text-sm text-red-600 bg-red-50 border border-red-100 rounded-lg px-3 py-2 mb-3">
              {uploadError}
            </div>
          )}
          <button
            type="submit"
            disabled={!file || !consent || uploading}
            className="w-full py-2 bg-sky-600 text-white text-sm rounded-lg hover:bg-sky-700 disabled:opacity-50"
          >
            {uploading ? "Uploading..." : "Submit contribution"}
          </button>
        </form>
      )}

      {/* Contributions */}
      <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-5 mb-5">
        <h2 className="font-semibold text-gray-900 mb-3">Contributions</h2>
        {project.contributions.length === 0 && (
          <p className="text-sm text-gray-400">No contributions yet.</p>
        )}
        <div className="space-y-3">
          {project.contributions.map((c) => (
            <div
              key={c.id}
              className="border border-gray-100 rounded-xl p-3 flex items-start justify-between gap-3"
            >
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <span
                    className={`text-xs px-2 py-0.5 rounded-full ${
                      c.status === "approved"
                        ? "bg-green-50 text-green-700"
                        : c.status === "rejected"
                        ? "bg-red-50 text-red-700"
                        : "bg-gray-100 text-gray-600"
                    }`}
                  >
                    {c.status}
                  </span>
                  {c.order_index !== null && (
                    <span className="text-xs text-gray-400">#{c.order_index}</span>
                  )}
                </div>
                <p className="text-sm text-gray-700">
                  {c.caption || "(no caption)"}
                </p>
                <p className="text-xs text-gray-400 mt-1">
                  {c.video_url}
                  {c.duration_seconds && ` — ${c.duration_seconds.toFixed(1)}s`}
                </p>
              </div>
              {c.status === "pending" && (
                <div className="flex gap-2">
                  <button
                    onClick={() => moderate(c.id, "approved")}
                    className="text-xs px-3 py-1 bg-green-600 text-white rounded-lg hover:bg-green-700"
                  >
                    Approve
                  </button>
                  <button
                    onClick={() => moderate(c.id, "rejected")}
                    className="text-xs px-3 py-1 border border-red-200 text-red-600 rounded-lg hover:bg-red-50"
                  >
                    Reject
                  </button>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Stitch button */}
      {project.status !== "stitched" && approvedCount > 0 && (
        <button
          onClick={stitch}
          disabled={stitching}
          className="w-full py-3 bg-green-600 text-white rounded-xl font-medium hover:bg-green-700 disabled:opacity-50"
        >
          {stitching
            ? "Stitching..."
            : `🎬 Stitch ${approvedCount} approved clips`}
        </button>
      )}
    </div>
  );
}