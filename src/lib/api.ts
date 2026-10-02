const configuredBaseUrl = import.meta.env.VITE_API_BASE_URL?.trim() ?? "";

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly code?: string,
    public readonly questionCode?: string,
    public readonly reason?: string,
  ) {
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
    const detail = body?.detail;
    if (detail && typeof detail === "object" && !Array.isArray(detail)) {
      const validation = detail as { code?: unknown; question_code?: unknown; reason?: unknown };
      throw new ApiError(
        response.status,
        typeof validation.code === "string" ? validation.code : undefined,
        typeof validation.question_code === "string" ? validation.question_code : undefined,
        typeof validation.reason === "string" ? validation.reason : undefined,
      );
    }
    throw new ApiError(response.status, typeof detail === "string" ? detail : undefined);
  }
  return body as T;
}
