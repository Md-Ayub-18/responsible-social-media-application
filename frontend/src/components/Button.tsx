import type { ButtonHTMLAttributes } from "react";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  loading?: boolean;
  variant?: "primary" | "secondary";
}

export default function Button({
  loading,
  variant = "primary",
  children,
  disabled,
  className = "",
  ...props
}: ButtonProps) {
  const base =
    "w-full py-2 rounded-lg text-sm font-medium transition-colors disabled:opacity-60 disabled:cursor-not-allowed";
  const styles =
    variant === "primary"
      ? "bg-sky-600 text-white hover:bg-sky-700"
      : "bg-gray-100 text-gray-700 hover:bg-gray-200";

  return (
    <button
      {...props}
      disabled={disabled || loading}
      className={`${base} ${styles} ${className}`}
    >
      {loading ? "Please wait..." : children}
    </button>
  );
}