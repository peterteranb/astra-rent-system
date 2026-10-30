import { useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import Layout from "../../components/Layout";
import Alert from "../../components/Alert";
import Badge from "../../components/Badge";
import FormErrors from "../../components/FormErrors";
import { getStaffReturns, returnRental } from "../../api/staff";
import { errorsFrom } from "../../utils/friendlyErrors";
import { useLoader } from "../../utils/useLoader";
import { formatDateTime } from "../../utils/format";
import "../account/AccountPage.css";
import EquipmentImage from "../../components/EquipmentImage";

export default function ReturnFormPage() {
  const { rentalId } = useParams();
  const navigate = useNavigate();
  const { data, loading, error } = useLoader(getStaffReturns);
  const [note, setNote] = useState("");
  const [errors, setErrors] = useState([]);
  const [sending, setSending] = useState(false);

  const rental = data?.find((r) => r.id === Number(rentalId));

  const submit = async (e) => {
    e.preventDefault();
    setErrors([]);
    setSending(true);
    try {
      const { message } = await returnRental(rental.id, { note });
      navigate("/staff/returns", { state: { message } });
    } catch (err) {
      setErrors(errorsFrom(err));
      setSending(false);
    }
  };

  const title = rental ? `Devolver ${rental.equipment.inventory_id}` : "Devolver equipo";

  return (
    <Layout title={title}>
      {loading && !data && <p className="list-message">Cargando…</p>}
      {error && <Alert>{error}</Alert>}

      {data && !rental && (
        <section className="card account">
          <Alert type="info">Esta renta ya no está pendiente de devolución.</Alert>
          <Link className="btn btn--secondary" style={{ marginTop: 16 }} to="/staff/returns">
            Volver a devoluciones
          </Link>
        </section>
      )}

      {rental && (
        <section className="card account">
          <EquipmentImage inventoryId={rental.equipment.inventory_id} name={rental.equipment.name} />
          <p>{rental.equipment.name}</p>
          <p className="lead">
            Cliente {rental.client} · <Badge tone={rental.status}>{rental.status_label}</Badge> ·
            vence el {formatDateTime(rental.end)}.
          </p>

          <form className="form" onSubmit={submit} noValidate>
            <FormErrors errors={errors} />

            <div className="field">
              <label className="field__label" htmlFor="note">Observación</label>
              <div className="field__control">
                <textarea id="note" className="field__input" rows={3} maxLength={200}
                  value={note} onChange={(e) => setNote(e.target.value)} />
              </div>
              <p className="field__hint">Cuenta cómo llegó el equipo.</p>
            </div>

            <button className="btn btn--primary" type="submit" disabled={sending}>
              {sending ? "Guardando…" : "Registrar devolución"}
            </button>
            <Link className="btn btn--secondary" to="/staff/returns">Volver a devoluciones</Link>
          </form>
        </section>
      )}
    </Layout>
  );
}
