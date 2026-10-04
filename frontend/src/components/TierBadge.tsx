interface TierBadgeProps {
  tier: string | null | undefined;
  size?: "sm" | "md";
}

const STYLES: Record<string, { label: string; emoji: string; color: string }> = {
  child: { label: "Child", emoji: "🧸", color: "bg-green-50 text-green-700 border-green-200" },
  teen: { label: "Teen", emoji: "🎒", color: "bg-blue-50 text-blue-700 border-blue-200" },
  adult: { label: "Adult", emoji: "✓", color: "bg-sky-50 text-sky-700 border-sky-200" },
};

export default function TierBadge({ tier, size = "sm" }: TierBadgeProps) {
  if (!tier || !STYLES[tier]) return null;
  const s = STYLES[tier];
  const cls =
    size === "sm"
      ? "text-[10px] px-1.5 py-0.5"
      : "text-xs px-2 py-0.5";
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full border font-medium ${s.color} ${cls}`}
    >
      <span>{s.emoji}</span>
      <span>{s.label}</span>
    </span>
  );
}