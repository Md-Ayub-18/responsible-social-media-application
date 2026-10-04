import {
  createContext,
  useContext,
  useEffect,
  useState,
} from "react";
import type { ReactNode } from "react";
import { api, setToken } from "../lib/api";
import type { TokenResponse, User } from "../lib/types";

interface AuthContextValue {
  user: User | null;
  loading: boolean;
  needsDOB: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (
    email: string,
    username: string,
    password: string,
    displayName?: string
  ) => Promise<void>;
  setDateOfBirth: (dob: string) => Promise<User>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (!token) {
      setLoading(false);
      return;
    }
    api
      .get<User>("/api/v1/auth/me")
      .then(setUser)
      .catch(() => {
        setToken(null);
        setUser(null);
      })
      .finally(() => setLoading(false));
  }, []);

  const needsDOB = !!user && (user.date_of_birth === null || !user.is_active);

  async function login(email: string, password: string) {
    const data = await api.post<TokenResponse>("/api/v1/auth/login", {
      email,
      password,
    });
    setToken(data.access_token);
    setUser(data.user);
  }

  async function register(
    email: string,
    username: string,
    password: string,
    displayName?: string
  ) {
    const data = await api.post<TokenResponse>("/api/v1/auth/register", {
      email,
      username,
      password,
      display_name: displayName || username,
    });
    setToken(data.access_token);
    setUser(data.user);
  }

  async function setDateOfBirth(dob: string): Promise<User> {
    const res = await api.post<{ user: User }>("/api/v1/auth/set-date-of-birth", {
      date_of_birth: dob,
    });
    setUser(res.user);
    return res.user;
  }

  function logout() {
    setToken(null);
    setUser(null);
  }

  return (
    <AuthContext.Provider
      value={{ user, loading, needsDOB, login, register, setDateOfBirth, logout }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside AuthProvider");
  return ctx;
}