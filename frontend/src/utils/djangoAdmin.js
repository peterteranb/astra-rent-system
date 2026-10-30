export const DJANGO_ADMIN = import.meta.env.DEV
  ? "http://localhost:8080/admin/"
  : "/admin/";
