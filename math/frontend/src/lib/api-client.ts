const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export async function apiClient<T>(endpoint: string, options?: RequestInit): Promise<T> {
    const response = await fetch(`${BASE_URL}${endpoint}`, {
        headers: {
            "Content-Type": "application/json",
            ...options?.headers,
        },
        ...options,
    });

    if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: "Unknown error" }));
        throw new Error(error.detail || `API Error: ${response.statusText}`);
    }

    return response.json();
}
