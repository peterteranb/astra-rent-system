import { Link } from "react-router-dom";
import tigre from "../assets/images/brand/tigre-con-carrito.png";
import "./ErrorPage.css";
export default function ErrorPage({ code, label, title, text, plain = false }) {
  const back = plain ? (
    <a className="btn btn--primary" href="/">
      <Arrow />
      Volver al inicio
    </a>
  ) : (
    <Link className="btn btn--primary" to="/">
      <Arrow />
      Volver al inicio
    </Link>
  );
  return (
    <div className="error-page">
      <header className="error-page__header">
        <p className="error-page__brand">
          Sergio<span>Corp</span>
        </p>
        <p className="error-page__activity">Renta de mesas y sillas</p>
      </header>
      <main className="error-page__main">
        <img
          className="error-page__art"
          src={tigre}
          alt="Tigre de SergioCorp con un carrito"
        />
        <div className="error-page__body">
          <div className="error-page__status">
            <span className="error-page__kind">{label}</span>
            <span className="error-page__code">{code}</span>
          </div>
          <h1 className="error-page__title">{title}</h1>
          <p className="error-page__text">{text}</p>
          {back}
        </div>
      </main>
      <footer className="error-page__footer">
        <hr className="divider" />
        <div className="error-page__origin">
          <span className="error-page__signature">SergioCorp</span>
          <span>Santa Cruz de la Sierra, Bolivia</span>
        </div>
      </footer>
    </div>
  );
}
function Arrow() {
  return (
    <svg
      width="18"
      height="18"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2.5"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path d="M19 12H5M12 19l-7-7 7-7" />
    </svg>
  );
}
