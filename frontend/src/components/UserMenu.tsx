import { useEffect, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import TierBadge from "./TierBadge";

export default function UserMenu() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  // Close on outside click
  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  if (!user) return null;

  function handleLogout() {
    setOpen(false);
    logout();
    navigate("/login");
  }

  return (
    <div ref={menuRef} className="relative">
      <button
        onClick={() => setOpen((o) => !o)}
        className="flex items-center gap-2 text-sm text-gray-600 hover:text-sky-600 transition-colors press"
      >
        <span>@{user.username}</span>
        <TierBadge tier={user.account_tier} size="sm" />
      </button>

      {open && (
        <div className="absolute right-0 top-full mt-2 w-56 bg-white border border-gray-100 rounded-xl shadow-lg py-2 z-50 animate-fade-in">
          <Link
            to={`/u/${user.username}`}
            onClick={() => setOpen(false)}
            className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 transition-colors"
          >
            👤 My profile
          </Link>

          <Link
            to="/settings"
            onClick={() => setOpen(false)}
            className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 transition-colors"
          >
            ⚙️ Settings
          </Link>

          {user.is_moderator && (
            <>
              <div className="my-1 border-t border-gray-100" />
              <Link
                to="/moderation"
                onClick={() => setOpen(false)}
                className="block px-4 py-2 text-sm text-sky-700 hover:bg-sky-50 transition-colors"
              >
                🛡️ Moderation
              </Link>
            </>
          )}

          <div className="my-1 border-t border-gray-100" />

          <button
            onClick={handleLogout}
            className="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50 transition-colors"
          >
            🚪 Logout
          </button>
        </div>
      )}
    </div>
  );
}