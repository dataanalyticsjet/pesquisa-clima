const configuredBaseUrl = import.meta.env.VITE_API_BASE_URL?.trim() ?? "";

export class ApiError extends Error {
  constructor(public readonly status: number, public readonly code?: string) {
    super("A solicitação não pôde ser concluída.");
    this.name = "ApiError";
  }
}

export function apiUrl(path: string) {
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  return `${configuredBaseUrl.replace(/\/$/, "")}${normalizedPath}`;
}

export async function apiRequest<T>(path: string, init: RequestInit = {}): Promise<T> {
  let response: Response;
  try {
    response = await fetch(apiUrl(path), {
      ...init,
      credentials: "include",
      headers: {
        ...(init.body ? { "Content-Type": "application/json" } : {}),
        ...init.headers,
      },
    });
  } catch {
    throw new ApiError(0, "NETWORK_ERROR");
  }

  const body = await response.json().catch(() => undefined) as { detail?: unknown } | undefined;
  if (!response.ok) {
    throw new ApiError(response.status, typeof body?.detail === "string" ? body.detail : undefined);
  }
  return body as T;
}
