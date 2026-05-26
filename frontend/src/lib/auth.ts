export type User = {
  id: number;
  full_name: string;
  username: string;
  role: "admin" | "operator" | "viewer";
  is_active: boolean;
};

export function getStoredUser(): User | null {
  if (typeof window === "undefined") return null;
  const raw = localStorage.getItem("visionid_user");
  return raw ? JSON.parse(raw) : null;
}

export function setAuth(token: string, user: User) {
  localStorage.setItem("visionid_token", token);
  localStorage.setItem("visionid_user", JSON.stringify(user));
}

export function clearAuth() {
  localStorage.removeItem("visionid_token");
  localStorage.removeItem("visionid_user");
}
