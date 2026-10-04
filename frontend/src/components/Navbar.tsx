import { Link, useLocation } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import UserMenu from "./UserMenu";

export default function Navbar() {
  const { user } = useAuth();
  const location = useLocation();

  if (!user) return null;

  const links = [
    { to: "/feed", label: "Feed" },
    { to: "/communities", label: "Communities" },
    { to: "/interests", label: "Interests" },
    { to: "/focus-modes", label: "Focus Modes" },
    { to: "/stitch", label: "Stitch" },
  ];

  return (
    <nav className="bg-white border-b border-gray-200 px-6 py-3 flex items-center justify-between">
      <div className="flex items-center gap-6">
        <Link to="/feed" className="text-lg font-bold text-sky-600">
          Verity
        </Link>
        {links.map((l) => (
          <Link
            key={l.to}
            to={l.to}
            className={`text-sm transition-colors press ${
              location.pathname === l.to
                ? "text-sky-600 font-semibold"
                : "text-gray-600 hover:text-gray-900"
            }`}
          >
            {l.label}
          </Link>
        ))}
      </div>

      <div className="flex items-center gap-4">
        <Link
          to="/post/new"
          className="text-sm px-3 py-1.5 bg-sky-600 text-white rounded-lg hover:bg-sky-700 transition-colors press"
        >
          + New Post
        </Link>
        <UserMenu />
      </div>
    </nav>
  );
}