import { Routes, Route } from "react-router-dom";
import LoginPage from "./pages/public/LoginPage";
import CatalogPage from "./pages/client/CatalogPage";
import RentFormPage from "./pages/client/RentFormPage";
import RentalConfirmationPage from "./pages/client/RentalConfirmationPage";
import ClientRentalsPage from "./pages/client/ClientRentalsPage";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<LoginPage />} />
      <Route path="/catalogo" element={<CatalogPage />} />
      <Route path="/rentar" element={<RentFormPage />} />
      <Route path="/confirmacion" element={<RentalConfirmationPage />} />
    </Routes>
  );
}
