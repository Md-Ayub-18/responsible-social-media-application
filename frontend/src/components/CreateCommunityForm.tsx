import { useState } from "react";
import type { FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { api, ApiError } from "../lib/api";
import type { Community, Interest } from "../lib/types";
import EmojiPickerInput from "./EmojiPickerInput";

interface Props {
  interests: Interest[];
  onCancel: () => void;
  onCreated: () => void;
}

export default function CreateCommunityForm({ interests, onCancel, onCreated }: Props) {
  const navigate = useNavigate();
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [emoji, setEmoji] = useState("🌐");
  const [slug, setSlug] = useState(interests[0]?.slug ?? "");
  const [isPublic, setIsPublic] = useState(true);
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!name.trim() || !slug) return;
    setCreating(true);
    setError(null);
    try {
      const created = await api.post<Community>("/api/v1/communities", {
        name: name.trim(),
        description: description.trim() || null,
        emoji: emoji || null,
        interest_slug: slug,
        is_public: isPublic,
      });
      onCreated();
      navigate(`/c/${created.slug}`);
    } catch (err) {
      const msg =
        err instanceof ApiError
          ? typeof err.detail === "string"
            ? err.detail
            : "Failed to create community"
          : "Failed to create community";
      setError(msg);
      setCreating(false);
    }
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="bg-white border border-gray-200 rounded-2xl p-5 mb-6"
    >
      <h2 className="font-semibold text-gray-900 mb-4">Create a community</h2>

      {/* Emoji + Name */}
      <div className="flex gap-3 mb-3 items-start">
        <EmojiPickerInput value={emoji} onChange={setEmoji} />
        <input
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="Community name (e.g., Tech Talk)"
          className="flex-1 border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-sky-500"
          required
          minLength={3}
          maxLength={100}
          autoFocus
        />
      </div>

      {/* Description */}
      <textarea
        value={description}
        onChange={(e) => setDescription(e.target.value)}
        placeholder="What is this community about?"
        rows={3}
        className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm mb-4 resize-none focus:outline-none focus:ring-2 focus:ring-sky-500"
      />

      {/* Interest */}
      <p className="text-xs font-medium text-gray-600 mb-2">Interest topic:</p>
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

      {/* Public toggle */}
      <label className="flex items-center gap-2 text-sm text-gray-700 mb-4">
        <input
          type="checkbox"
          checked={isPublic}
          onChange={(e) => setIsPublic(e.target.checked)}
        />
        <span>Public (anyone can find and join)</span>
      </label>

      {error && (
        <div className="text-sm text-red-600 bg-red-50 border border-red-100 rounded-lg px-3 py-2 mb-3">
          {error}
        </div>
      )}

      {/* Actions */}
      <div className="flex items-center justify-end gap-3">
        <button
          type="button"
          onClick={onCancel}
          className="text-sm px-4 py-2 text-gray-600 hover:text-gray-900 transition-colors"
        >
          Cancel
        </button>
        <button
          type="submit"
          disabled={creating || !name.trim()}
          className="text-sm px-5 py-2 bg-sky-600 text-white rounded-lg hover:bg-sky-700 disabled:opacity-50 transition-colors"
        >
          {creating ? "Creating..." : "Create community"}
        </button>
      </div>
    </form>
  );
}