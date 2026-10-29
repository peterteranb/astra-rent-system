import { api } from "./client";

export const searchClients = (query = "") =>
  api(`/staff/clients/?${new URLSearchParams({ q: query })}`);
export const createClient = (clientData) =>
  api("/staff/clients/", { method: "POST", body: clientData });
export const createWalkInRental = (rentalData) =>
  api("/staff/rentals/", { method: "POST", body: rentalData });
export const getStaffReservations = () => api("/staff/reservations/");
export const pickupReservation = (rentalId, paidNow = false) =>
  api(`/staff/rentals/${rentalId}/pickup/`, {
    method: "POST",
    body: { paid_now: paidNow },
  });
export const getStaffReturns = () => api("/staff/returns/");
export const returnRental = (rentalId, returnData) =>
  api(`/staff/rentals/${rentalId}/return/`, { method: "POST", body: returnData });
export const getStaffDebts = () => api("/staff/debts/");
export const payDebt = (debtId) =>
  api(`/staff/debts/${debtId}/pay/`, { method: "POST", body: {} });
