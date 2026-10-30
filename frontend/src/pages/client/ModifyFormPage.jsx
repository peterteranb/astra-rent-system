import { useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import Layout from "../../components/Layout";
import Alert from "../../components/Alert";
import FormErrors from "../../components/FormErrors";
import PeriodFields from "../../components/PeriodFields";
import { useAuth } from "../../auth/AuthContext";
import { getStaffReservations } from "../../api/staff";
import { getMyRentals, modifyRental } from "../../api/rentals";
import { errorsFrom } from "../../utils/friendlyErrors";
import { useLoader } from "../../utils/useLoader";
import { formatDateTime, PICKUP_FROM, RETURN_UNTIL } from "../../utils/format";
import "../account/AccountPage.css";
const STAFF_ROLES = ["operador", "administrador"];
const toPeriod = (r) => ({
  start_date: r.start.slice(0, 10),
  start_time: r.start.slice(11, 16),
  end_date: r.end.slice(0, 10),
  end_time: r.end.slice(11, 16),
});
export default function ModifyFormPage() {
  const { rentalId } = useParams();
  const { user } = useAuth();
  const navigate = useNavigate();
  const staff = STAFF_ROLES.includes(user.role);
  const back = staff ? "/staff/reservations" : "/my-rentals";
  const { data, loading, error } = useLoader(() =>
    staff ? getStaffReservations() : getMyRentals(),
  );
  const rental = (staff ? data : data?.rentals)?.find(
    (r) => r.id === Number(rentalId),
  );
  const [edits, setEdits] = useState(null);
  const [errors, setErrors] = useState([]);
  const [sending, setSending] = useState(false);
  const values = edits ?? (rental ? toPeriod(rental) : null);
  const change = (f) => (e) => setEdits({ ...values, [f]: e.target.value });
  const can =
    rental &&
    rental.status === "reserved" &&
    (staff || rental.client_can_change);
  const submit = async (e) => {
    e.preventDefault();
    setErrors([]);
    if (Object.values(values).some((v) => !v))
      return setErrors([
        "Completa la fecha y la hora de recojo y de devolución.",
      ]);
    setSending(true);
    try {
      const { message } = await modifyRental(rental.id, values);
      navigate(back, { state: { message } });
    } catch (err) {
      setErrors(errorsFrom(err));
      setSending(false);
    }
  };
  return (
    <Layout
      title={
        rental
          ? `Modificar la reserva de ${rental.equipment.inventory_id}`
          : "Modificar reserva"
      }
    >
      {loading && !data && <p className="list-message">Cargando reserva…</p>}
      {error && <Alert>{error}</Alert>}
      {data && !can && (
        <section className="card account">
          <Alert type="info">
            {rental && rental.status === "reserved"
              ? "Ya no puedes modificar en línea; comunícate con la tienda."
              : "Esta reserva ya no se puede modificar."}
          </Alert>
          <Link className="btn btn--secondary" to={back}>
            Volver
          </Link>
        </section>
      )}
      {can && (
        <section className="card rental-card">
          <p>
            {rental.equipment.name}
            {staff && <> · reserva de {rental.client}</>}
          </p>
          <p className="lead">
            Ahora va del {formatDateTime(rental.start)} al{" "}
            {formatDateTime(rental.end)}. Recojo desde las {PICKUP_FROM} y
            devolución hasta las {RETURN_UNTIL}.
          </p>
          <form className="form" onSubmit={submit}>
            <FormErrors errors={errors} />
            <PeriodFields values={values} onChange={change} />
            <button className="btn btn--primary" disabled={sending}>
              {sending ? "Guardando…" : "Guardar cambios"}
            </button>
            <Link className="btn btn--secondary" to={back}>
              Volver
            </Link>
          </form>
        </section>
      )}
    </Layout>
  );
}
