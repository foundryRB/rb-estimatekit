/**
 * Base HTTP client — thin wrapper around fetch.
 *
 * BASE_URL defaults to '/api' (browser, proxied by Vite).
 * Set VITE_API_BASE_URL to override — e.g. 'http://localhost:8000/api'
 * for integration tests that hit the backend directly.
 */

const BASE_URL: string =
    (typeof import.meta !== 'undefined' && import.meta.env?.VITE_API_BASE_URL) ||
    (typeof process !== 'undefined' && process.env?.VITE_API_BASE_URL) ||
    '/api';

export class ApiError extends Error {
    constructor(
        public readonly status: number,
        public readonly detail: string,
    ) {
        super(detail);
        this.name = 'ApiError';
    }
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
    const url = `${BASE_URL}${path}`;
    const response = await fetch(url, {
        headers: { 'Content-Type': 'application/json', ...options?.headers },
        ...options,
    });

    if (!response.ok) {
        const body = await response.json().catch(() => ({ detail: response.statusText }));
        throw new ApiError(response.status, body.detail ?? body.error ?? response.statusText);
    }

    // 204 No Content — nothing to parse
    if (response.status === 204) {
        return undefined as T;
    }

    return response.json() as Promise<T>;
}

export function get<T>(path: string): Promise<T> {
    return request<T>(path, { method: 'GET' });
}

export function post<T>(path: string, body?: unknown): Promise<T> {
    return request<T>(path, {
        method: 'POST',
        body: body ? JSON.stringify(body) : undefined,
    });
}

export function put<T>(path: string, body?: unknown): Promise<T> {
    return request<T>(path, {
        method: 'PUT',
        body: body ? JSON.stringify(body) : undefined,
    });
}

export function del<T>(path: string): Promise<T> {
    return request<T>(path, { method: 'DELETE' });
}

/** Download a binary file as a Blob. */
export async function download(path: string): Promise<Blob> {
    const url = `${BASE_URL}${path}`;
    const response = await fetch(url);
    if (!response.ok) {
        throw new ApiError(response.status, response.statusText);
    }
    return response.blob();
}

/** Upload a file via multipart/form-data. */
export async function upload(path: string, file: File, fieldName = 'file'): Promise<void> {
    const url = `${BASE_URL}${path}`;
    const form = new FormData();
    form.append(fieldName, file);
    const response = await fetch(url, { method: 'POST', body: form });
    if (!response.ok) {
        const body = await response.json().catch(() => ({ detail: response.statusText }));
        throw new ApiError(response.status, body.detail ?? body.error ?? response.statusText);
    }
}
