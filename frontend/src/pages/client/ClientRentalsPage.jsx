import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import Layout from "../../components/Layout";
import FormErrors from "../../components/FormErrors";
import { getMyRentals, cancelRental } from "../../api/rentals";
import { errorsFrom } from "../../utils/friendlyErrors";
import "./ClientRentalsPage.css";
import Alert from "../../components/Alert.jsx";

// La API manda fechas ISO; se muestran en hora de La Paz
const formatDate = (iso) =>
  new Date(iso).toLocaleString("es-BO", {
    timeZone: "America/La_Paz",
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });

export default function ClientRentalsPage() {
  const [summary, setSummary] = useState({
    rentals: [],
    debts: [],
    debt_total: "0.00",
  });
  const [debtMessage, setDebtMessage] = useState("");
  const [loading, setLoading] = useState(true);
  const [errors, setErrors] = useState([]);
  const message = useLocation().state?.message;

  const load = useCallback(async () => {
    try {
      const { data, message } = await getMyRentals();
      setSummary(data);
      setDebtMessage(message);
    } catch (err) {
      setErrors(errorsFrom(err));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const cancel = async (rental) => {
    if (
      !window.confirm(
        `¿Cancelar la reserva de ${rental.equipment.inventory_id}?`,
      )
    )
      return;
    setErrors([]);
    try {
      await cancelRental(rental.id);
      await load();
    } catch (err) {
      setErrors(errorsFrom(err));
    }
  };

  return (
    <Layout title="Mis rentas">
      <div className="rentals-stripes" />

      <div className="rentals-heading">
        <div>
          <span className="eyebrow">MIS RENTAS</span>
          <h2>Tus reservas y pagos</h2>
        </div>
        {!loading && (
          <span className="rentals-count">{summary.rentals.length} rentas</span>
        )}
      </div>

      <FormErrors errors={errors} />

      {debtMessage && (
        <section className="rentals-debt">
          <strong>{debtMessage}</strong>
          <ul>
            {summary.debts.map((debt) => (
              <li key={debt.id}>
                {debt.reason_label} · {debt.equipment} · {debt.amount} Bs
              </li>
            ))}
          </ul>
        </section>
      )}

      {message && <Alert type="success">{message}</Alert>}

      {loading && <p className="rentals-message">Cargando tus rentas…</p>}
      {!loading && summary.rentals.length === 0 && (
        <p className="rentals-message">Todavía no tienes rentas.</p>
      )}

      <div className="rentals-list">
        {summary.rentals.map((rental) => (
          <article className="rental-card" key={rental.id}>
            <div className="rental-card__image">
              <img
                src={`/img/equipment/${rental.equipment.inventory_id}.jpg`}
                alt={rental.equipment.name}
                loading="lazy"
                onError={(e) => {
                  e.currentTarget.style.display = "none";
                }}
              />
            </div>

            <div className="rental-card__body">
              <p className="rental-card__code">
                {rental.equipment.inventory_id}
              </p>
              <h3>{rental.equipment.name}</h3>
              <p className="rental-card__dates">
                {formatDate(rental.start)} → {formatDate(rental.end)}
              </p>
              <div className="rental-card__badges">
                <span className={`rental-badge rental-badge--${rental.status}`}>
                  {rental.status_label}
                </span>
                <span
                  className={`rental-badge ${rental.is_paid ? "rental-badge--paid" : "rental-badge--pending"}`}
                >
                  {rental.payment_label}
                </span>
              </div>
            </div>

            <div className="rental-card__side">
              <strong>{rental.total_price} Bs</strong>
              {rental.client_can_change ? (
                <div className="rental-card__actions">
                  <Link
                    className="btn btn--secondary"
                    to={`/rentals/${rental.id}/modify`}
                  >
                    Modificar
                  </Link>
                  <button
                    className="btn btn--secondary"
                    type="button"
                    onClick={() => cancel(rental)}
                  >
                    Cancelar
                  </button>
                </div>
              ) : (
                rental.status === "reserved" && (
                  <small>Para cambiarla, comunícate con la tienda.</small>
                )
              )}
            </div>
          </article>
        ))}
      </div>
    </Layout>
  );
}
