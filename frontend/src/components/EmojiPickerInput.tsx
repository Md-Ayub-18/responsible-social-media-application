import { useEffect, useRef, useState } from "react";
import EmojiPicker, { Theme } from "emoji-picker-react";

interface EmojiPickerInputProps {
  value: string;
  onChange: (emoji: string) => void;
}

export default function EmojiPickerInput({ value, onChange }: EmojiPickerInputProps) {
  const [open, setOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  // Close on outside click
  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  function handleEmojiClick(data: any) {
    onChange(data.emoji);
    setOpen(false);
  }

  return (
    <div ref={containerRef} className="relative">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className="w-16 h-16 flex items-center justify-center text-3xl border-2 border-dashed border-gray-300 rounded-xl hover:border-sky-400 hover:bg-sky-50/40 transition-colors"
        title="Click to pick an emoji"
      >
        {value || "🌐"}
      </button>

      {open && (
        <div className="absolute top-full left-0 mt-2 z-50 shadow-2xl rounded-2xl overflow-hidden">
          <EmojiPicker
            onEmojiClick={handleEmojiClick}
            theme={Theme.LIGHT}
            width={340}
            height={400}
            searchDisabled={false}
            skinTonesDisabled={false}
            lazyLoadEmojis
          />
        </div>
      )}
    </div>
  );
}