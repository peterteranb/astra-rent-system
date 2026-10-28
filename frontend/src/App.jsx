import { Routes, Route } from "react-router-dom";
import LoginPage from "./pages/LoginPage";
import CatalogPage from "./pages/CatalogPage";
import RentFormPage from "./pages/RentFormPage";
import RentalConfirmationPage from "./pages/RentalConfirmationPage";

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