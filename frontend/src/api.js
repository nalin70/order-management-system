const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

const storage = {
  get access() {
    return localStorage.getItem("access");
  },
  get refresh() {
    return localStorage.getItem("refresh");
  },
  setSession(data) {
    localStorage.setItem("access", data.access);
    localStorage.setItem("refresh", data.refresh);
    localStorage.setItem("user", JSON.stringify({ email: data.email, role: data.role }));
  },
  clear() {
    localStorage.removeItem("access");
    localStorage.removeItem("refresh");
    localStorage.removeItem("user");
  },
};

async function refreshAccessToken() {
  if (!storage.refresh) return null;
  const response = await fetch(`${API_BASE_URL}/api/auth/refresh/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh: storage.refresh }),
  });
  if (!response.ok) {
    storage.clear();
    return null;
  }
  const data = await response.json();
  localStorage.setItem("access", data.access);
  return data.access;
}

async function parseResponse(response) {
  const text = await response.text();
  if (!text) return {};
  try {
    return JSON.parse(text);
  } catch {
    return { message: text };
  }
}

function errorMessage(data, fallback) {
  if (data?.message) return data.message;
  if (data?.detail) return data.detail;
  if (data?.errors) return JSON.stringify(data.errors);
  return fallback;
}

export async function apiRequest(path, options = {}) {
  const { method = "GET", body, auth = true } = options;
  const headers = { "Content-Type": "application/json", ...(options.headers || {}) };
  if (auth && storage.access) headers.Authorization = `Bearer ${storage.access}`;

  let response = await fetch(`${API_BASE_URL}${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });

  if (response.status === 401 && auth) {
    const newAccess = await refreshAccessToken();
    if (newAccess) {
      response = await fetch(`${API_BASE_URL}${path}`, {
        method,
        headers: { ...headers, Authorization: `Bearer ${newAccess}` },
        body: body ? JSON.stringify(body) : undefined,
      });
    }
  }

  const data = await parseResponse(response);
  if (!response.ok) {
    throw new Error(errorMessage(data, `Request failed with ${response.status}`));
  }
  return data;
}

export function normalizeList(payload) {
  if (Array.isArray(payload)) return payload;
  if (Array.isArray(payload?.data)) return payload.data;
  if (Array.isArray(payload?.results)) return payload.results;
  if (Array.isArray(payload?.data?.results)) return payload.data.results;
  return [];
}

export { storage };
