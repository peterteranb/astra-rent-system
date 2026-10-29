import { api } from "./client";

export function getMaintenanceEquipment(status = "") {
  const query = status ? `?${new URLSearchParams({ status })}` : "";
  return api(`/maintenance/equipment/${query}`);
}

export const reviewEquipment = (inventoryId, reviewData) =>
  api(`/maintenance/equipment/${encodeURIComponent(inventoryId)}/review/`, {
    method: "POST",
    body: reviewData,
  });
