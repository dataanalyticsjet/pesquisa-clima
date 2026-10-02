import { apiRequest } from "../lib/api";

export type AuthUser = { name: string; email: string; access_type: string; roles: string[] };
export type AuthMe = { authenticated: true; user: AuthUser };

export function getCurrentUser() {
  return apiRequest<AuthMe>("/api/auth/me");
}

export function requestEmailCode(email: string) {
  return apiRequest<{ message: string }>("/api/auth/external/request-code", {
    method: "POST",
    body: JSON.stringify({ email }),
  });
}

export function verifyEmailCode(email: string, code: string) {
  return apiRequest<{ authenticated: boolean }>("/api/auth/external/verify-code", {
    method: "POST",
    body: JSON.stringify({ email, code }),
  });
}

export function logout() {
  return apiRequest<{ authenticated: false }>("/api/auth/logout", { method: "POST" });
}
