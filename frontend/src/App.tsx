import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import type { ReactNode } from "react";
import { AuthProvider, useAuth } from "./contexts/AuthContext";
import Navbar from "./components/Navbar";
import LoginPage from "./pages/LoginPage";
import RegisterPage from "./pages/RegisterPage";
import FeedPage from "./pages/FeedPage";
import InterestsPage from "./pages/InterestsPage";
import FocusModesPage from "./pages/FocusModesPage";
import CreatePostPage from "./pages/CreatePostPage";   
import ModerationPage from "./pages/ModerationPage";
import ProfilePage from "./pages/ProfilePage";
import StitchListPage from "./pages/StitchListPage";
import StitchDetailPage from "./pages/StitchDetailPage";
import GuardianPage from "./pages/GuardianPage";
import DateOfBirthModal from "./components/DateOfBirthModal";
import CommunitiesPage from "./pages/CommunitiesPage";
import CommunityDetailPage from "./pages/CommunityDetailPage";
import SettingsPage from "./pages/SettingsPage";



function ModeratorOnly({ children }: { children: ReactNode }) {
  const { user, loading } = useAuth();
  if (loading) return <div className="p-8 text-gray-500">Loading...</div>;
  if (!user) return <Navigate to="/login" replace />;
  if (!user.is_moderator) return <Navigate to="/feed" replace />;
  return (
    <>
      <Navbar />
      {children}
    </>
  );
}

function Protected({ children }: { children: ReactNode }) {
  const { user, loading, needsDOB } = useAuth();
  if (loading) return <div className="p-8 text-gray-500">Loading...</div>;
  if (!user) return <Navigate to="/login" replace />;
  return (
    <>
      <Navbar />
      {needsDOB && <DateOfBirthModal />}
      {children}
    </>
  );
}

function PublicOnly({ children }: { children: ReactNode }) {
  const { user, loading } = useAuth();
  if (loading) return <div className="p-8 text-gray-500">Loading...</div>;
  if (user) return <Navigate to="/feed" replace />;
  return <>{children}</>;
}

function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<PublicOnly><LoginPage /></PublicOnly>} />
      <Route path="/register" element={<PublicOnly><RegisterPage /></PublicOnly>} />
      <Route path="/feed" element={<Protected><FeedPage /></Protected>} />
      <Route path="/interests" element={<Protected><InterestsPage /></Protected>} />
      <Route path="/focus-modes" element={<Protected><FocusModesPage /></Protected>} />
      <Route path="/post/new" element={<Protected><CreatePostPage /></Protected>} />
      <Route path="/moderation" element={<ModeratorOnly><ModerationPage /></ModeratorOnly>} />
      <Route path="/u/:username" element={<Protected><ProfilePage /></Protected>} />
      <Route path="/stitch" element={<Protected><StitchListPage /></Protected>} />
      <Route path="/stitch/:projectId" element={<Protected><StitchDetailPage /></Protected>} />
      <Route path="/guardian" element={<Protected><GuardianPage /></Protected>} />
      <Route path="*" element={<Navigate to="/feed" replace />} />
      <Route path="/communities" element={<Protected><CommunitiesPage /></Protected>} />
      <Route path="/c/:slug" element={<Protected><CommunityDetailPage /></Protected>} />
      <Route path="/settings" element={<Protected><SettingsPage /></Protected>} />
    </Routes>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </BrowserRouter>
  );
}