import { Routes, Route } from "react-router-dom";
import ProtectedRoute from "./components/ProtectedRoute";

import LoginPage from "./pages/public/LoginPage";
import ForgotPasswordPage from "./pages/public/ForgotPasswordPage";
import SignupPage from "./pages/public/SignupPage";
import ForbiddenPage from "./pages/public/ForbiddenPage";
import NotFoundPage from "./pages/public/NotFoundPage";

import CatalogPage from "./pages/client/CatalogPage";
import RentFormPage from "./pages/client/RentFormPage";
import PayRentalPage from "./pages/client/PayRentalPage";
import RentalConfirmationPage from "./pages/client/RentalConfirmationPage";
import ClientRentalsPage from "./pages/client/ClientRentalsPage";
import AccountPage from "./pages/account/AccountPage.jsx";
import ChangePasswordPage from "./pages/account/ChangePasswordPage.jsx";
import ModifyFormPage from "./pages/client/ModifyFormPage";

import StaffReservationsPage from "./pages/staff/StaffReservationsPage";
import StaffReturnsPage from "./pages/staff/StaffReturnsPage";
import ReturnFormPage from "./pages/staff/ReturnFormPage";
import WalkInRentalPage from "./pages/staff/WalkInRentalPage";
import NewClientPage from "./pages/staff/NewClientPage";
import StaffDebtsPage from "./pages/staff/StaffDebtsPage";

import MaintenancePage from "./pages/maintenance/MaintenancePage";
import ManagerDashboardPage from "./pages/manager/ManagerDashboardPage";
import EquipmentFormPage from "./pages/manager/EquipmentFormPage";

const guard = (element, roles) => (
  <ProtectedRoute roles={roles}>{element}</ProtectedRoute>
);

export default function App() {
  return (
    <Routes>
      {/* Públicas */}
      <Route path="/login" element={<LoginPage />} />
      <Route path="/forgot-password" element={<ForgotPasswordPage />} />
      <Route path="/signup" element={<SignupPage />} />
      <Route path="/403" element={<ForbiddenPage />} />

      {/* Cliente (cualquiera con sesión) */}
      <Route path="/" element={guard(<CatalogPage />)} />
      <Route path="/equipment/:inventoryId/rent" element={guard(<RentFormPage />)} />
      <Route path="/rentals/:rentalId/pay" element={guard(<PayRentalPage />)} />
      <Route path="/rentals/:rentalId" element={guard(<RentalConfirmationPage />)} />
      <Route path="/rentals/:rentalId/modify" element={guard(<ModifyFormPage />)} />
      <Route path="/my-rentals" element={guard(<ClientRentalsPage />, ["cliente"])} />
      <Route path="/account" element={guard(<AccountPage />)} />
      <Route path="/account/password" element={guard(<ChangePasswordPage />)} />

      {/* Operador */}
      <Route path="/staff/reservations" element={guard(<StaffReservationsPage />, ["operador"])} />
      <Route path="/staff/returns" element={guard(<StaffReturnsPage />, ["operador"])} />
      <Route path="/staff/returns/:rentalId" element={guard(<ReturnFormPage />, ["operador"])} />
      <Route path="/staff/walk-in" element={guard(<WalkInRentalPage />, ["operador"])} />
      <Route path="/staff/clients/new" element={guard(<NewClientPage />, ["operador"])} />
      <Route path="/staff/debts" element={guard(<StaffDebtsPage />, ["operador"])} />

      {/* Mantenimiento */}
      <Route path="/maintenance" element={guard(<MaintenancePage />, ["mantenimiento"])} />

      {/* Administrador (solo lo que no es el admin de Django) */}
      <Route path="/manager" element={guard(<ManagerDashboardPage />, ["administrador"])} />
      <Route path="/equipment/new" element={guard(<EquipmentFormPage />, ["administrador"])} />

      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  );
}
