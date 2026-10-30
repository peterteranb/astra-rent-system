import { api } from "./client";

export const getManagerDashboard = () => api("/manager/dashboard/");
export const createEquipment = (equipmentData) =>
  api("/admin/equipment/", { method: "POST", body: equipmentData });