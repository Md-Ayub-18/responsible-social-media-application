import { useAuth } from "../contexts/AuthContext";
import TierBadge from "../components/TierBadge";

export default function SettingsPage() {
  const { user } = useAuth();
  if (!user) return null;

  return (
    <div className="max-w-2xl mx-auto px-4 py-6">
      <h1 className="text-2xl font-bold text-gray-900 mb-1">Settings</h1>
      <p className="text-sm text-gray-500 mb-6">Manage your account and preferences.</p>

      <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6 mb-4">
        <h2 className="font-semibold text-gray-900 mb-4">Profile</h2>
        <div className="space-y-3 text-sm">
          <div className="flex items-center justify-between">
            <span className="text-gray-500">Username</span>
            <span className="font-medium text-gray-900">@{user.username}</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-gray-500">Email</span>
            <span className="font-medium text-gray-900">{user.email}</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-gray-500">Display name</span>
            <span className="font-medium text-gray-900">{user.display_name || user.username}</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-gray-500">Account tier</span>
            <TierBadge tier={user.account_tier} size="sm" />
          </div>
          <div className="flex items-center justify-between">
            <span className="text-gray-500">Date of birth</span>
            <span className="font-medium text-gray-900">
              {user.date_of_birth || "Not set"}
            </span>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
        <h2 className="font-semibold text-gray-900 mb-2">Coming soon</h2>
        <p className="text-sm text-gray-500">
          Profile pictures, avatar upload, password change, and other preferences
          will be available here in a future update.
        </p>
      </div>
    </div>
  );
}