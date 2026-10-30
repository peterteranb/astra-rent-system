import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import Layout from "../../components/Layout";
import FormErrors from "../../components/FormErrors";
import { getMyRentals, payRental } from "../../api/rentals";
import { errorsFrom } from "../../utils/friendlyErrors";
import { formatDate } from "../../utils/formatDate";
import "./RentalFlow.css";
import EquipmentImage from "../../components/EquipmentImage";

export default function PayRentalPage() {
  const { rentalId } = useParams();
  const navigate = useNavigate();
  const [rental, setRental] = useState(null);
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [errors, setErrors] = useState([]);

  useEffect(() => {
    getMyRentals()
      .then(({ data }) => {
        const found = data.rentals.find((r) => String(r.id) === rentalId);
        if (!found) {
          setErrors(["No encontramos esta renta."]);
        } else if (found.is_paid || found.status !== "reserved") {
          // Ya pagada o ya no es una reserva: no hay nada que pagar aquí
          navigate(`/rentals/${found.id}`, { replace: true });
        } else {
          setRental(found);
        }
      })
      .catch((err) => setErrors(errorsFrom(err)))
      .finally(() => setLoading(false));
  }, [rentalId, navigate]);

  // approved es lo que respondería la pasarela simulada (ENT-48: una pasarela real se conecta sin cambiar la renta).
  const simulate = async (approved) => {
    setErrors([]);
    setSending(true);
    try {
      const { message } = await payRental(rental.id, approved);
      navigate(`/rentals/${rental.id}`, {
        state: { message, approved },
        replace: true,
      });
    } catch (err) {
      setErrors(errorsFrom(err));
      setSending(false);
    }
  };

  return (
    <Layout title="Pagar con QR">
      <section className="card flow-card">
        <p className="eyebrow">PAGO DE TU RENTA</p>
        <h1 className="flow-title">Pagar con QR</h1>

        <FormErrors errors={errors} />
        {loading && <p className="flow-message">Cargando tu renta…</p>}

        {rental && (
          <>
            <EquipmentImage
              inventoryId={rental.equipment.inventory_id}
              name={rental.equipment.name}
            />
            <dl className="flow-details">
              <dt>Equipo</dt>
              <dd>
                {rental.equipment.inventory_id} · {rental.equipment.name}
              </dd>
              <dt>Recojo</dt>
              <dd>{formatDate(rental.start)}</dd>
              <dt>Devolución</dt>
              <dd>{formatDate(rental.end)}</dd>
              <dt>Total</dt>
              <dd>
                {rental.rental_days} día{rental.rental_days === 1 ? "" : "s"} ×{" "}
                {rental.daily_price} Bs ={" "}
                <strong>{rental.total_price} Bs</strong>
              </dd>
            </dl>

            <div className="qr-box" aria-label="Código QR de pago">
              <span>QR</span>
              {/* Poné la foto en frontend/public/img/qr.png: tapa el cuadrado punteado */}
              <img
                src="/img/qr.png"
                alt="Código QR de pago"
                onError={(e) => {
                  e.currentTarget.style.display = "none";
                }}
              />
            </div>
            <p className="flow-hint">
              Pago simulado: elige si la pasarela aprueba o rechaza el pago. Si
              falla, la reserva queda hecha y pagas en la tienda al recoger.
            </p>

            <div className="flow-actions">
              <button
                className="btn btn--primary"
                type="button"
                disabled={sending}
                onClick={() => simulate(true)}
              >
                Simular pago exitoso
              </button>
              <button
                className="btn btn--secondary"
                type="button"
                disabled={sending}
                onClick={() => simulate(false)}
              >
                Simular pago fallido
              </button>
            </div>
          </>
        )}
      </section>
    </Layout>
  );
}
