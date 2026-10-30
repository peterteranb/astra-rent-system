export const PICKUP_FROM = "18:00"; // el recojo es desde esta hora
export const RETURN_UNTIL = "09:00"; // la devolución es hasta esta hora
export const MAX_DAYS = 5;

export function formatMoney(amount) {
  return `${Number(amount).toLocaleString("es-BO", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })} Bs`;
}

// "2026-10-30T18:00:00-04:00" -> "30/10/2026 18:00"
export function formatDateTime(iso) {
  if (!iso) return "";
  return new Date(iso)
    .toLocaleString("es-BO", {
      timeZone: "America/La_Paz",
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
      hour12: false,
    })
    .replace(",", "");
}
