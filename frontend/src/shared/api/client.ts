import { ApiError } from "./types";
import type { ProblemDetails } from "./types";

const API_BASE_URL =
  (import.meta.env as ImportMetaEnv & { VITE_API_URL?: string }).VITE_API_URL ||
  "/api/v1";

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let problem: ProblemDetails;
    try {
      problem = await response.json();
    } catch {
      problem = {
        title: "Erreur réseau ou serveur indisponible",
        status: response.status,
        detail: response.statusText,
      };
    }
    throw new ApiError(problem);
  }
  if (response.status === 204) {
    return {} as T;
  }
  return response.json();
}

export const apiClient = {
  async get<T>(endpoint: string): Promise<T> {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      headers: { Accept: "application/json" },
    });
    return handleResponse<T>(response);
  },

  async post<T>(endpoint: string, body?: unknown): Promise<T> {
    const isFormData = body instanceof FormData;
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: "POST",
      headers: isFormData ? {} : { "Content-Type": "application/json" },
      body: isFormData ? body : JSON.stringify(body),
    });
    return handleResponse<T>(response);
  },
};
