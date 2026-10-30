import logo from "../assets/images/brand/logo-header.png";
import tigre from "../assets/images/brand/tigre-con-carrito.png";
import "./AuthLayout.css";

export default function AuthLayout({ heading, text, children }) {
  return (
    <div className="auth">
      <header className="auth__header">
        <img className="auth__logo" src={logo} alt="SergioCorp" />
        <span className="auth__help">¿Necesitas ayuda?</span>
      </header>

      <div className="auth__body">
        <aside className="auth__brand">
          <img className="auth__art" src={tigre} alt="Tigre de SergioCorp con un carrito" />
          <h2 className="auth__brand-title">{heading}</h2>
          <p className="auth__brand-text">{text}</p>
          <div className="auth__stripes auth__stripes--light" aria-hidden="true" />
          <div className="auth__values">
            <span>DESDE SANTA CRUZ DE LA SIERRA BOLIVIA</span>
            <span>MESAS Y SILLAS</span>
          </div>
        </aside>

        <main className="auth__main">{children}</main>
      </div>

      <div className="auth__stripes auth__stripes--gold" aria-hidden="true" />
      <footer className="auth__footer">
        © 2026 SergioCorp · Santa Cruz de la Sierra Bolivia
      </footer>
    </div>
  );
}