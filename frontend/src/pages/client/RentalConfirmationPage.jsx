import { useEffect, useState } from "react";
import { Link, useLocation, useParams } from "react-router-dom";
import Layout from "../../components/Layout";
import Alert from "../../components/Alert";
import FormErrors from "../../components/FormErrors";
import { getMyRentals } from "../../api/rentals";
import { errorsFrom } from "../../utils/friendlyErrors";
import { formatDate } from "../../utils/formatDate";
import "./RentalFlow.css";
import EquipmentImage from "../../components/EquipmentImage";

export default function RentalConfirmationPage() {
  const { rentalId } = useParams();
  const location = useLocation();
  const [rental, setRental] = useState(null);
  const [loading, setLoading] = useState(true);
  const [errors, setErrors] = useState([]);

  useEffect(() => {
    getMyRentals()
      .then(({ data }) => {
        const found = data.rentals.find((r) => String(r.id) === rentalId);
        if (found) setRental(found);
        else setErrors(["No encontramos esta renta."]);
      })
      .catch((err) => setErrors(errorsFrom(err)))
      .finally(() => setLoading(false));
  }, [rentalId]);

  const { message, approved } = location.state || {};

  return (
    <Layout title="Renta confirmada">
      <section className="card flow-card">
        <p className="eyebrow">TU RESERVA</p>
        <h1 className="flow-title">Renta confirmada</h1>

        {message && <Alert type={approved ? "success" : "info"}>{message}</Alert>}
        <FormErrors errors={errors} />
        {loading && <p className="flow-message">Cargando tu renta…</p>}

        {rental && (
          <>
            <EquipmentImage inventoryId={rental.equipment.inventory_id} name={rental.equipment.name} />
            <dl className="flow-details">
              <dt>Equipo</dt>
              <dd>{rental.equipment.inventory_id} · {rental.equipment.name}</dd>
              <dt>Recojo</dt>
              <dd>{formatDate(rental.start)}</dd>
              <dt>Devolución</dt>
              <dd>{formatDate(rental.end)}</dd>
              <dt>Total</dt>
              <dd>
                {rental.rental_days} día{rental.rental_days === 1 ? "" : "s"} × {rental.daily_price} Bs ={" "}
                {rental.total_price} Bs
              </dd>
              <dt>Pago</dt>
              <dd>
                <span className={`rental-badge ${rental.is_paid ? "rental-badge--paid" : "rental-badge--pending"}`}>
                  {rental.payment_label}
                </span>
              </dd>
              {rental.is_paid && (
                <>
                  <dt>Forma de pago</dt>
                  <dd>{rental.payment_method_label}</dd>
                </>
              )}
            </dl>

            <p className="flow-hint">Entregamos los equipos desde las 18:00.</p>

            <div className="flow-actions">
              <Link className="btn btn--primary" to="/">Volver al catálogo</Link>
              <Link className="btn btn--secondary" to="/my-rentals">Ver mis rentas</Link>
              {!rental.is_paid && rental.status === "reserved" && (
                <Link className="btn btn--secondary" to={`/rentals/${rental.id}/pay`}>
                  Intentar pagar de nuevo
                </Link>
              )}
            </div>
          </>
        )}
      </section>
    </Layout>
  );
}
