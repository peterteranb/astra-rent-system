export class ApiError extends Error {
  constructor(errors, status) {
    super(errors.join(" "));
    this.errors = errors;
    this.status = status;
  }
}

function readCookie(name) {
  const match = document.cookie.match(new RegExp(`(?:^|; )${name}=([^;]*)`));
  return match ? decodeURIComponent(match[1]) : "";
}

export async function api(path, { method = "GET", body } = {}) {
  const response = await fetch(`/api${path}`, {
    method,
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": readCookie("csrftoken"),
    },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  let payload = {};
  try { payload = await response.json(); } catch { /* respuesta sin JSON */ }
  if (!response.ok) {
    throw new ApiError(payload.errors ?? ["Algo salió mal. Inténtalo de nuevo."], response.status);
  }
  return payload; // { data, message }
}