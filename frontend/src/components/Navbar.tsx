import { Link, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";

export default function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  function handleLogout() {
    logout();
    navigate("/login");
  }

  if (!user) return null;

  const links = [
    { to: "/feed", label: "Feed" },
    { to: "/interests", label: "Interests" },
    { to: "/focus-modes", label: "Focus Modes" },
    { to: "/stitch", label: "Stitch" },
    { to: "/guardian", label: "Guardian" },
  ];

  const moderatorLinks = user.is_moderator
    ? [{ to: "/moderation", label: "Moderation" }]
    : [];

  const allLinks = [...links, ...moderatorLinks];

  return (
    <nav className="bg-white border-b border-gray-200 px-6 py-3 flex items-center justify-between">
      <div className="flex items-center gap-6">
        <Link to="/feed" className="text-lg font-bold text-sky-600">
          Verity
        </Link>
        {allLinks.map((l) => (
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

        <Link
          to={`/u/${user.username}`}
          className="text-sm text-gray-600 hover:text-sky-600 transition-colors"
        >
          @{user.username}
        </Link>

        <button
          onClick={handleLogout}
          className="text-sm text-gray-500 hover:text-gray-800 transition-colors press"
        >
          Logout
        </button>
      </div>
    </nav>
  );
}