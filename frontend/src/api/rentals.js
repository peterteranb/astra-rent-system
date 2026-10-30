import { api } from "./client";

export const createRental = (rentalData) =>
  api("/rentals/", { method: "POST", body: rentalData });
export const payRental = (rentalId, approved = true) =>
  api(`/rentals/${rentalId}/pay/`, { method: "POST", body: { approved } });
export const getMyRentals = () => api("/my-rentals/");
export const modifyRental = (rentalId, rentalData) =>
  api(`/rentals/${rentalId}/modify/`, { method: "POST", body: rentalData });
export const cancelRental = (rentalId) =>
  api(`/rentals/${rentalId}/cancel/`, { method: "POST", body: {} });
