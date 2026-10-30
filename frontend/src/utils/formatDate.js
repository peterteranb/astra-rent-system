// La API manda fechas ISO; se muestran en hora de La Paz
export const formatDate = (iso) =>
  new Date(iso).toLocaleString("es-BO", {
    timeZone: "America/La_Paz",
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });