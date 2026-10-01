interface FocusModeBannerProps {
  modeName: string | null;
  focusApplied: boolean;
  interestSlugs: string[];
}

const INTEREST_LABELS: Record<string, string> = {
  learning: "Learning",
  sports: "Sports",
  art: "Art",
  technology: "Technology",
  entertainment: "Entertainment",
  personal: "Personal",
  social_causes: "Social Causes",
};

export default function FocusModeBanner({
  modeName,
  focusApplied,
  interestSlugs,
}: FocusModeBannerProps) {
  return (
    <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-5 mb-5">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-xs uppercase tracking-wider text-gray-400 mb-1">
            Current focus
          </p>
          <p className="text-lg font-semibold text-gray-900">
            {focusApplied && modeName
              ? `${modeName} mode`
              : "No focus mode"}
          </p>
        </div>
        {focusApplied && (
          <span className="text-xs text-sky-700 bg-sky-50 px-3 py-1 rounded-full border border-sky-100">
            active
          </span>
        )}
      </div>

      {interestSlugs.length > 0 && (
        <div className="flex flex-wrap gap-2 mt-4">
          {interestSlugs.map((slug) => (
            <span
              key={slug}
              className="text-xs px-3 py-1 rounded-full bg-gray-100 text-gray-700"
            >
              {INTEREST_LABELS[slug] ?? slug}
            </span>
          ))}
        </div>
      )}

      {interestSlugs.length === 0 && (
        <p className="text-sm text-gray-500 mt-3">
          Select some interests to see posts here.
        </p>
      )}
    </div>
  );
}