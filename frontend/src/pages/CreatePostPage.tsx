import { useEffect, useState } from "react";
import type { ChangeEvent, FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { api, ApiError } from "../lib/api";
import type { Interest } from "../lib/types";

interface UploadResponse {
  url: string;
  kind: "image" | "video";
  size_bytes: number;
}

export default function CreatePostPage() {
  const navigate = useNavigate();
  const [interests, setInterests] = useState<Interest[]>([]);
  const [text, setText] = useState("");
  const [slug, setSlug] = useState<string>("");
  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [previewKind, setPreviewKind] = useState<"image" | "video" | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // load interests
  useEffect(() => {
    api
      .get<Interest[]>("/api/v1/interests/")
      .then((list) => {
        setInterests(list);
        if (list.length > 0) setSlug(list[0].slug);
      })
      .catch((err) => {
        setError(
          err instanceof ApiError
            ? typeof err.detail === "string"
              ? err.detail
              : "Failed to load interests"
            : "Failed to load interests"
        );
      })
      .finally(() => setLoading(false));
  }, []);

  // manage preview URL lifecycle
  useEffect(() => {
    if (!file) {
      setPreviewUrl(null);
      setPreviewKind(null);
      return;
    }
    const url = URL.createObjectURL(file);
    setPreviewUrl(url);
    setPreviewKind(file.type.startsWith("video/") ? "video" : "image");
    return () => URL.revokeObjectURL(url);
  }, [file]);

  function handleFile(e: ChangeEvent<HTMLInputElement>) {
    setError(null);
    const f = e.target.files?.[0] ?? null;

    if (!f) {
      setFile(null);
      return;
    }

    const allowed = ["image/jpeg", "image/png", "image/webp", "image/gif",
                     "video/mp4", "video/quicktime", "video/webm"];
    if (!allowed.includes(f.type)) {
      setError("Only images (jpg/png/webp/gif) or videos (mp4/mov/webm) are allowed.");
      return;
    }
    if (f.size > 100 * 1024 * 1024) {
      setError("File too large — max 100 MB.");
      return;
    }

    setFile(f);
  }

  function removeFile() {
    setFile(null);
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!text.trim() && !file) {
      setError("Add some text or a media file.");
      return;
    }
    if (!slug) {
      setError("Pick an interest.");
      return;
    }

    setError(null);
    setSubmitting(true);
    try {
      const mediaUrls: string[] = [];

      // Upload file first if present
      if (file) {
        const uploaded = await api.upload<UploadResponse>(
          "/api/v1/uploads/media",
          file
        );
        mediaUrls.push(uploaded.url);
      }

      // Create the post
      await api.post("/api/v1/posts", {
        text: text.trim() || "(media post)",
        interest_slug: slug,
        media_urls: mediaUrls,
      });

      navigate("/feed");
    } catch (err) {
      const msg =
        err instanceof ApiError
          ? typeof err.detail === "string"
            ? err.detail
            : "Failed to create post"
          : "Failed to create post";
      setError(msg);
      setSubmitting(false);
    }
  }

  if (loading) {
    return <div className="p-8 text-center text-gray-400">Loading...</div>;
  }

  return (
    <div className="max-w-2xl mx-auto px-4 py-6">
      <h1 className="text-2xl font-bold text-gray-900 mb-1">Create a post</h1>
      <p className="text-sm text-gray-500 mb-6">
        Posts are analyzed for safety and AI-generated content in the
        background.
      </p>

      <form
        onSubmit={handleSubmit}
        className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6"
      >
        {/* Media upload */}
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Add photo or video
        </label>

        {!file ? (
          <label className="flex flex-col items-center justify-center border-2 border-dashed border-gray-200 rounded-xl px-4 py-10 cursor-pointer hover:border-sky-400 hover:bg-sky-50/40 transition-colors mb-5">
            <span className="text-4xl mb-2">📷</span>
            <span className="text-sm font-medium text-gray-700">
              Click to choose a file
            </span>
            <span className="text-xs text-gray-400 mt-1">
              JPG, PNG, WEBP, GIF, MP4, MOV, WEBM — up to 100 MB
            </span>
            <input
              type="file"
              accept="image/*,video/*"
              onChange={handleFile}
              className="hidden"
            />
          </label>
        ) : (
          <div className="mb-5">
            <div className="rounded-xl overflow-hidden bg-black flex items-center justify-center max-h-96">
              {previewKind === "video" && previewUrl ? (
                <video src={previewUrl} controls className="max-h-96 w-full" />
              ) : previewUrl ? (
                <img
                  src={previewUrl}
                  alt="preview"
                  className="max-h-96 w-full object-contain"
                />
              ) : null}
            </div>
            <div className="flex items-center justify-between mt-2">
              <span className="text-xs text-gray-500">
                {file.name} — {(file.size / 1024 / 1024).toFixed(1)} MB
              </span>
              <button
                type="button"
                onClick={removeFile}
                className="text-xs text-red-600 hover:underline"
              >
                Remove
              </button>
            </div>
          </div>
        )}

        {/* Interest */}
        <label className="block text-sm font-medium text-gray-700 mb-2">
          What's this about?
        </label>
        <div className="flex flex-wrap gap-2 mb-5">
          {interests.map((i) => {
            const on = i.slug === slug;
            return (
              <button
                type="button"
                key={i.id}
                onClick={() => setSlug(i.slug)}
                className={`text-sm px-3 py-1.5 rounded-full border transition-colors ${
                  on
                    ? "bg-sky-100 border-sky-300 text-sky-800 font-medium"
                    : "bg-white border-gray-200 text-gray-600 hover:border-gray-300"
                }`}
              >
                {i.emoji} {i.name}
              </button>
            );
          })}
        </div>

        {/* Caption */}
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Caption
        </label>
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Say something..."
          rows={4}
          maxLength={5000}
          className="w-full border border-gray-300 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-sky-500 focus:border-transparent resize-none"
        />
        <p className="text-xs text-gray-400 mt-1 text-right">
          {text.length} / 5000
        </p>

        {error && (
          <div className="mt-4 text-sm text-red-600 bg-red-50 border border-red-100 rounded-lg px-3 py-2">
            {error}
          </div>
        )}

        <div className="flex items-center justify-end gap-3 mt-5">
          <button
            type="button"
            onClick={() => navigate("/feed")}
            className="text-sm px-4 py-2 text-gray-600 hover:text-gray-900"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={submitting || (!text.trim() && !file)}
            className="text-sm px-5 py-2 bg-sky-600 text-white rounded-lg hover:bg-sky-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {submitting ? "Posting..." : "Post"}
          </button>
        </div>
      </form>
    </div>
  );
}