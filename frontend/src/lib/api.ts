const BASE_URL = "";

export class ApiError extends Error {
  status: number;
  detail: any;
  constructor(status: number, detail: any) {
    super(typeof detail === "string" ? detail : "Request failed");
    this.status = status;
    this.detail = detail;
  }
}

function getToken(): string | null {
  return localStorage.getItem("access_token");
}

export function setToken(token: string | null) {
  if (token) localStorage.setItem("access_token", token);
  else localStorage.removeItem("access_token");
}

export function isLoggedIn(): boolean {
  return !!getToken();
}

async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const headers = new Headers(options.headers || {});
  const token = getToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);
  if (
    options.body &&
    !(options.body instanceof FormData) &&
    !headers.has("Content-Type")
  ) {
    headers.set("Content-Type", "application/json");
  }

  const resp = await fetch(`${BASE_URL}${path}`, { ...options, headers });

  if (resp.status === 204) return undefined as T;

  const text = await resp.text();
  const data = text ? JSON.parse(text) : null;

   if (!resp.ok) {
    // Friendly handling for rate limit errors
    if (resp.status === 429) {
      const retryAfter = resp.headers.get("retry-after");
      const secs = retryAfter ? parseInt(retryAfter, 10) : 60;
      const msg =
        secs < 60
          ? `Too many requests. Please wait ${secs} seconds and try again.`
          : `Too many requests. Please wait ${Math.ceil(secs / 60)} minute(s) and try again.`;
      throw new ApiError(429, msg);
    }
    throw new ApiError(resp.status, data?.detail ?? data);
  }

  return data as T;
}

export const api = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body?: any) =>
    request<T>(path, {
      method: "POST",
      body: body instanceof FormData ? body : JSON.stringify(body ?? {}),
    }),
  patch: <T>(path: string, body?: any) =>
    request<T>(path, {
      method: "PATCH",
      body: JSON.stringify(body ?? {}),
    }),
  delete: <T>(path: string) => request<T>(path, { method: "DELETE" }),
  upload: <T>(path: string, file: File) => {   // ← add this whole method
    const fd = new FormData();
    fd.append("file", file);
    return request<T>(path, { method: "POST", body: fd });
  },
};