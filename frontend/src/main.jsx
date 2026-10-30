import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import { AuthProvider } from "./auth/AuthContext";
import App from "./App.jsx";
import ErrorBoundary from "./components/ErrorBoundary";
import "./styles/index.css"

createRoot(document.getElementById("root")).render(
  <StrictMode>
    <BrowserRouter>
      <ErrorBoundary>
        <AuthProvider><App /></AuthProvider>
      </ErrorBoundary>
    </BrowserRouter>
  </StrictMode>
);
