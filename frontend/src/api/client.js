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

const CSRF_EXPIRED = "La sesión de seguridad venció";

async function send(path, method, body) {
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
  return { response, payload };
}

export async function api(path, { method = "GET", body } = {}) {
  let { response, payload } = await send(path, method, body);

  // Llave de seguridad vieja: se pide una nueva y se reintenta una sola vez.
  if (response.status === 403 && payload.errors?.[0]?.startsWith(CSRF_EXPIRED)) {
    await send("/csrf/", "GET");
    ({ response, payload } = await send(path, method, body));
  }

  // Sesión vencida: avisa a la app para que vuelva al login.
  if (response.status === 401 && !path.startsWith("/auth/")) {
    window.dispatchEvent(new Event("session-expired"));
  }

  if (!response.ok) {
    throw new ApiError(payload.errors ?? ["Algo salió mal. Inténtalo de nuevo."], response.status);
  }
  return payload; // { data, message }
}