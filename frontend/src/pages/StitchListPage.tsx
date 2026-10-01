import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api, ApiError } from "../lib/api";
import type { Interest, StitchProject } from "../lib/types";

export default function StitchListPage() {
  const navigate = useNavigate();
  const [projects, setProjects] = useState<StitchProject[]>([]);
  const [interests, setInterests] = useState<Interest[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [slug, setSlug] = useState("");
  const [creating, setCreating] = useState(false);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const [projs, ints] = await Promise.all([
        api.get<StitchProject[]>("/api/v1/stitch/projects"),
        api.get<Interest[]>("/api/v1/interests/"),
      ]);
      setProjects(projs);
      setInterests(ints);
      if (ints.length > 0 && !slug) setSlug(ints[0].slug);
    } catch (err) {
      setError(
        err instanceof ApiError
          ? typeof err.detail === "string"
            ? err.detail
            : "Failed to load projects"
          : "Failed to load projects"
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
    if (!title.trim() || !slug) return;
    setCreating(true);
    try {
      const created = await api.post<StitchProject>("/api/v1/stitch/projects", {
        title: title.trim(),
        description: description.trim() || null,
        interest_slug: slug,
      });
      navigate(`/stitch/${created.id}`);
    } catch (err) {
      const msg =
        err instanceof ApiError
          ? typeof err.detail === "string"
            ? err.detail
            : "Failed to create project"
          : "Failed to create project";
      alert(msg);
      setCreating(false);
    }
  }

  return (
    <div className="max-w-3xl mx-auto px-4 py-6">
      <div className="flex items-center justify-between mb-2">
        <h1 className="text-2xl font-bold text-gray-900">Stitch Studio</h1>
        <button
          onClick={() => setShowCreate((s) => !s)}
          className="text-sm px-3 py-1.5 bg-sky-600 text-white rounded-lg hover:bg-sky-700"
        >
          {showCreate ? "Cancel" : "+ New project"}
        </button>
      </div>
      <p className="text-sm text-gray-500 mb-6">
        Collaborate on a shared video. Contributors submit clips, the moderator
        reviews and combines approved ones into one final output.
      </p>

      {showCreate && (
        <form
          onSubmit={handleCreate}
          className="bg-white border border-gray-200 rounded-2xl p-5 mb-6"
        >
          <h2 className="font-semibold text-gray-900 mb-4">New project</h2>
          <input
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Title (e.g., Community cleanup highlights)"
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm mb-3 focus:outline-none focus:ring-2 focus:ring-sky-500"
            required
            minLength={3}
          />
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="What is this project about?"
            rows={3}
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm mb-4 resize-none focus:outline-none focus:ring-2 focus:ring-sky-500"
          />
          <p className="text-xs font-medium text-gray-600 mb-2">Topic:</p>
          <div className="flex flex-wrap gap-2 mb-4">
            {interests.map((i) => (
              <button
                type="button"
                key={i.id}
                onClick={() => setSlug(i.slug)}
                className={`text-xs px-3 py-1 rounded-full border transition-colors ${
                  i.slug === slug
                    ? "bg-sky-100 border-sky-300 text-sky-800"
                    : "bg-white border-gray-200 text-gray-600 hover:border-gray-300"
                }`}
              >
                {i.emoji} {i.name}
              </button>
            ))}
          </div>
          <button
            type="submit"
            disabled={creating || !title.trim()}
            className="w-full py-2 bg-sky-600 text-white text-sm rounded-lg hover:bg-sky-700 disabled:opacity-50"
          >
            {creating ? "Creating..." : "Create project"}
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

      {!loading && !error && projects.length === 0 && (
        <div className="text-center py-16 text-gray-400">
          <p className="text-4xl mb-3">🎬</p>
          <p>No stitch projects yet.</p>
          <p className="text-xs mt-2">Create one to get started.</p>
        </div>
      )}

      {!loading && !error && projects.length > 0 && (
        <div className="space-y-3">
          {projects.map((p) => (
            <Link
              key={p.id}
              to={`/stitch/${p.id}`}
              className="block bg-white rounded-2xl border border-gray-100 shadow-sm p-5 hover:border-gray-300 transition-colors"
            >
              <div className="flex items-start justify-between gap-3 mb-2">
                <h3 className="font-semibold text-gray-900">{p.title}</h3>
                <span
                  className={`text-xs px-2 py-0.5 rounded-full ${
                    p.status === "stitched"
                      ? "bg-green-50 text-green-700 border border-green-100"
                      : p.status === "open"
                      ? "bg-sky-50 text-sky-700 border border-sky-100"
                      : "bg-gray-50 text-gray-600 border border-gray-100"
                  }`}
                >
                  {p.status}
                </span>
              </div>
              {p.description && (
                <p className="text-sm text-gray-500 line-clamp-2">{p.description}</p>
              )}
              <div className="flex items-center gap-3 mt-3 text-xs text-gray-400">
                <span>#{p.interest_slug}</span>
                {p.stitched_video_url && (
                  <span className="text-green-600">✓ stitched</span>
                )}
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}