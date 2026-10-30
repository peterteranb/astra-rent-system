import { NavLink, Link } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import logo from "../assets/images/brand/logo-header.png";
import "./Layout.css";

// El admin de Django vive en el puerto 8080 mientras programas y en el mismo sitio en producción.
import { DJANGO_ADMIN } from "../utils/djangoAdmin";
// Mismo menú que base.html: el administrador ve todo lo del personal.
function linksFor(role) {
  const isAdmin = role === "administrador";
  const can = (needed) => isAdmin || role === needed;
  const isStaff = can("operador") || can("mantenimiento");

  const links = [{ to: "/", label: "Catálogo", end: true }];
  if (!isStaff) links.push({ to: "/my-rentals", label: "Mis rentas" });
  if (can("operador")) {
    links.push(
      { to: "/staff/clients/new", label: "Nuevo cliente" },
      { to: "/staff/walk-in", label: "Renta en tienda" },
      { to: "/staff/reservations", label: "Reservas por entregar" },
      { to: "/staff/returns", label: "Devoluciones" },
      { to: "/staff/debts", label: "Deudas" },
    );
  }
  if (can("mantenimiento"))
    links.push({ to: "/maintenance", label: "Mantenimiento" });
  if (isAdmin) {
    links.push(
      { to: "/manager", label: "Panel" },
      { to: "/equipment/new", label: "Registrar equipo" },
    );
  }
  links.push({ to: "/account", label: "Mi cuenta" });
  return links;
}

export default function Layout({ title, children }) {
  const { user, logout } = useAuth();

  return (
    <div className="layout">
      <header className="layout__header">
        <div className="layout__top">
          <Link to="/" aria-label="Ir al inicio">
            <img className="layout__logo" src={logo} alt="SergioCorp" />
          </Link>
          <div className="layout__user">
            <span>{user.first_name || user.username}</span>
            <button
              className="btn btn--secondary layout__logout"
              type="button"
              onClick={logout}
            >
              Cerrar sesión
            </button>
          </div>
        </div>

        <nav className="layout__nav" aria-label="Menú principal">
          {linksFor(user.role).map(({ to, label, end }) => (
            <NavLink key={to} to={to} end={end}>
              {label}
            </NavLink>
          ))}
          {user.role === "administrador" && <a href={DJANGO_ADMIN}>Admin</a>}
        </nav>
      </header>

      <main className="layout__main">
        {title && <h1 className="layout__title">{title}</h1>}
        {children}
      </main>
    </div>
  );
}
