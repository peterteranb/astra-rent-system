import { useEffect, useState } from "react";
import Layout from "../../components/Layout";
import Alert from "../../components/Alert";
import ReviewCard from "./ReviewCard";
import { getMaintenanceEquipment } from "../../api/maintenance";
import { errorsFrom } from "../../utils/friendlyErrors";
import "./MaintenancePage.css";

// Los equipos dados de baja no aparecen: su estado ya no cambia.
const FILTERS = [
  ["", "Todos"],
  ["available", "Disponible"],
  ["in_review", "En revisión"],
  ["in_repair", "En reparación"],
];

export default function MaintenancePage() {
  const [status, setStatus] = useState("");
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [version, setVersion] = useState(0); // sube para volver a pedir la lista

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError("");
    getMaintenanceEquipment(status)
      .then(({ data }) => !cancelled && setItems(data))
      .catch((err) => !cancelled && setError(errorsFrom(err)[0]))
      .finally(() => !cancelled && setLoading(false));
    return () => {
      cancelled = true;
    };
  }, [status, version]);

  const saved = (text) => {
    setMessage(text);
    setVersion((v) => v + 1);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  return (
    <Layout title="Mantenimiento">
      {message && <Alert type="success">{message}</Alert>}

      <section className="card maint-filter">
        <div className="field">
          <label className="field__label" htmlFor="status-filter">
            Estado
          </label>
          <div className="field__control">
            <select
              id="status-filter"
              className="field__input"
              value={status}
              onChange={(e) => {
                setStatus(e.target.value);
                setMessage("");
              }}
            >
              {FILTERS.map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
          </div>
        </div>
      </section>

      {loading && <p className="maint-message">Cargando equipos…</p>}
      {error && <Alert>{error}</Alert>}
      {!loading && !error && items.length === 0 && (
        <p className="maint-message">No hay equipos con ese estado.</p>
      )}

      <ul className="maint-list">
        {items.map((item) => (
          // La clave incluye el estado: al cambiarlo, el formulario se arma de nuevo con sus opciones.
          <ReviewCard
            key={`${item.inventory_id}-${item.status}`}
            item={item}
            onSaved={saved}
          />
        ))}
      </ul>
    </Layout>
  );
}
