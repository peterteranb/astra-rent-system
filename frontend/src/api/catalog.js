import { api } from "./client";

export function getCatalog(filters = {}) {
  const query = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") {
      query.set(key, value);
    }
  });
  const suffix = query.size ? `?${query.toString()}` : "";
  return api(`/catalog/${suffix}`);
}
