import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import Layout from "../../components/Layout";
import Alert from "../../components/Alert";
import FormErrors from "../../components/FormErrors";
import PeriodFields from "../../components/PeriodFields";
import { getCatalog } from "../../api/catalog";
import { createRental } from "../../api/rentals";
import { errorsFrom } from "../../utils/friendlyErrors";
import { formatMoney, PICKUP_FROM, RETURN_UNTIL, MAX_DAYS } from "../../utils/format";
import EquipmentImage from "../../components/EquipmentImage";
import "./RentalFlow.css";

// Los días son los que hay entre la fecha de recojo y la de devolución (igual que el servidor).
function countDays(from, to) {
  if (!from || !to) return 0;
  const diff = (new Date(`${to}T00:00:00`) - new Date(`${from}T00:00:00`)) / 86400000;
  return Math.round(diff);
}

export default function RentFormPage() {
  const { inventoryId } = useParams();
  const navigate = useNavigate();

  const [equipment, setEquipment] = useState(null);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState("");
  const [errors, setErrors] = useState([]);
  const [sending, setSending] = useState(false);
  const [period, setPeriod] = useState({
    start_date: "",
    start_time: PICKUP_FROM,
    end_date: "",
    end_time: RETURN_UNTIL,
  });

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    getCatalog({ q: inventoryId })
      .then(({ data }) => {
        if (cancelled) return;
        const found = data.results.find((item) => item.inventory_id === inventoryId);
        if (found) setEquipment(found);
        else setLoadError("Este equipo no existe o no está disponible en este momento.");
      })
      .catch((err) => !cancelled && setLoadError(errorsFrom(err)[0]))
      .finally(() => !cancelled && setLoading(false));
    return () => { cancelled = true; };
  }, [inventoryId]);

  const change = (field) => (e) => setPeriod({ ...period, [field]: e.target.value });

  const submit = async (e) => {
    e.preventDefault();
    setErrors([]);
    if (Object.values(period).some((value) => !value)) {
      setErrors(["Completa la fecha y la hora de recojo y de devolución."]);
      return;
    }
    setSending(true);
    try {
      const { data: rental } = await createRental({ equipment: inventoryId, ...period });
      navigate(`/rentals/${rental.id}/pay`, { state: { rental } });
    } catch (err) {
      setErrors(errorsFrom(err));
      setSending(false);
    }
  };

  if (loading) {
    return (
      <Layout title="Rentar">
        <p className="flow-message">Cargando equipo…</p>
      </Layout>
    );
  }

  if (!equipment) {
    return (
      <Layout title="Rentar">
        <section className="card rental-card">
          <Alert title="No se puede rentar este equipo">{loadError}</Alert>
          <div className="rental-actions" style={{ marginTop: 16 }}>
            <Link className="btn btn--secondary" to="/">Volver al catálogo</Link>
          </div>
        </section>
      </Layout>
    );
  }

  const days = countDays(period.start_date, period.end_date);
  const price = Number(equipment.daily_price);

  return (
    <Layout title={`Rentar ${equipment.inventory_id}`}>
      <section className="card rental-card">
        <EquipmentImage inventoryId={equipment.inventory_id} name={equipment.name} />
        <p className="lead">{equipment.name} · {formatMoney(price)} por día</p>

        <form className="form" onSubmit={submit} noValidate>
          <Alert type="info" title="Horario de recojo y devolución">
            Recojo desde las {PICKUP_FROM}. Devolución hasta las {RETURN_UNTIL}. Máximo {MAX_DAYS} días.
          </Alert>

          <FormErrors errors={errors} />

          <PeriodFields values={period} onChange={change} />

          {days >= 1 && days <= MAX_DAYS && (
            <div className="rental-summary" aria-live="polite">
              <span className="rental-summary__label">
                {days} {days === 1 ? "día" : "días"} × {formatMoney(price)}
              </span>
              <strong className="rental-summary__total">{formatMoney(days * price)}</strong>
            </div>
          )}

          <div className="rental-actions">
            <button className="btn btn--primary" type="submit" disabled={sending}>
              {sending ? "Continuando…" : "Continuar al pago"}
            </button>
            <Link className="btn btn--secondary" to="/">Volver al catálogo</Link>
          </div>
        </form>
      </section>
    </Layout>
  );
}
