import { useState } from "react";
import { useAuth } from "../contexts/AuthContext";

interface BreakReminderProps {
  todayMinutes: number;
  limitMinutes: number;
  isChild: boolean;
}

export default function BreakReminder({
  todayMinutes,
  limitMinutes,
  isChild,
}: BreakReminderProps) {
  const { logout } = useAuth();
  const [dismissed, setDismissed] = useState(false);

  if (dismissed) return null;

  const handleDismiss = () => {
    if (isChild) {
      // Children can't dismiss — force logout
      logout();
    } else {
      setDismissed(true);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl">
        <div className="text-center mb-5">
          <div className="text-5xl mb-3">⏰</div>
          <h2 className="text-xl font-bold text-gray-900">
            Time for a break
          </h2>
          <p className="text-sm text-gray-500 mt-2">
            You've been on Verity for <strong>{todayMinutes} minutes</strong>{" "}
            today.
            {limitMinutes > 0 && (
              <> Your daily limit is {limitMinutes} minutes.</>
            )}
          </p>
        </div>

        <div className="bg-sky-50 border border-sky-100 rounded-xl px-4 py-3 mb-5 text-sm text-sky-900">
          {isChild
            ? "Ask a parent or guardian if you want to keep browsing. Rest and play are important too."
            : "Rest your eyes, stretch, and come back when you're ready. Your feed will be here."}
        </div>

        <button
          onClick={handleDismiss}
          className="w-full py-2.5 rounded-lg text-sm font-medium transition-colors bg-sky-600 text-white hover:bg-sky-700"
        >
          {isChild ? "Sign out" : "I'll take a break later"}
        </button>
      </div>
    </div>
  );
}