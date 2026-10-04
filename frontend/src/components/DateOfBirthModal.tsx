import { useState } from "react";
import type { FormEvent } from "react";
import { useAuth } from "../contexts/AuthContext";
import Input from "./Input";
import Button from "./Button";

export default function DateOfBirthModal() {
  const { setDateOfBirth } = useAuth();
  const [dob, setDob] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    if (!dob) {
      setError("Please enter your date of birth");
      return;
    }
    setLoading(true);
    try {
      await setDateOfBirth(dob);
    } catch (err: any) {
      setError(
        typeof err?.detail === "string" ? err.detail : "Failed to save date of birth"
      );
      setLoading(false);
    }
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl">
        <div className="text-center mb-5">
          <div className="text-4xl mb-2">📅</div>
          <h2 className="text-xl font-bold text-gray-900">
            One more thing
          </h2>
          <p className="text-sm text-gray-500 mt-1">
            We need your date of birth to set up the right safety features for you.
          </p>
        </div>

        <form onSubmit={handleSubmit}>
          <Input
            label="Date of birth"
            type="date"
            value={dob}
            onChange={(e) => setDob(e.target.value)}
            required
            max={new Date().toISOString().split("T")[0]}
            autoFocus
          />

          <div className="bg-sky-50 border border-sky-100 rounded-lg px-3 py-2 mb-4 text-xs text-sky-900">
            We don't show your birth date to anyone. It's only used to
            determine your account type (child, teen, or adult).
          </div>

          {error && (
            <div className="mb-4 text-sm text-red-600 bg-red-50 border border-red-100 rounded-lg px-3 py-2">
              {error}
            </div>
          )}

          <Button type="submit" loading={loading}>
            Continue
          </Button>
        </form>
      </div>
    </div>
  );
}