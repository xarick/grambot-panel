const BASE = "/api/v1";

export class ApiError extends Error {
  constructor(detail, status) {
    super(detail);
    this.detail = detail;
    this.status = status;
  }
}

export async function request(method, path, body) {
  const init = {
    method,
    credentials: "include",
    headers: { "Content-Type": "application/json" },
  };
  if (body !== undefined) {
    init.body = JSON.stringify(body);
  }

  const res = await fetch(`${BASE}${path}`, init);

  if (res.status === 204) return null;

  if (!res.ok) {
    let detail = res.statusText;
    try {
      const data = await res.json();
      detail = data.detail || detail;
    } catch (_) {}
    if (res.status === 401) {
      window.dispatchEvent(new Event("auth:unauthorized"));
    }
    throw new ApiError(detail, res.status);
  }

  return res.json();
}

export async function upload(path, formData) {
  // Let the browser set the multipart Content-Type (with its boundary).
  const res = await fetch(`${BASE}${path}`, {
    method: "POST",
    credentials: "include",
    body: formData,
  });

  if (!res.ok) {
    let detail = res.statusText;
    try {
      const data = await res.json();
      detail = data.detail || detail;
    } catch (_) {}
    if (res.status === 401) {
      window.dispatchEvent(new Event("auth:unauthorized"));
    }
    throw new ApiError(detail, res.status);
  }

  return res.json();
}
