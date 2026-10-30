import { useState } from "react";
import { Link, useLocation } from "react-router-dom";
import Layout from "../../components/Layout";
import Alert from "../../components/Alert";
import DataTable from "../../components/DataTable";
import PaymentBadge from "../../components/PaymentBadge";
import { getStaffReservations, pickupReservation } from "../../api/staff";
import { cancelRental } from "../../api/rentals";
import { errorsFrom } from "../../utils/friendlyErrors";
import { useLoader } from "../../utils/useLoader";
import { formatDateTime, formatMoney } from "../../utils/format";
import OrderSelect from "../../components/OrderSelect";

export default function StaffReservationsPage() {
  const [order, setOrder] = useState("");
  const { data, loading, error, reload } = useLoader(() => getStaffReservations(order), [order]);
  const [busy, setBusy] = useState(false);
  const fromModify = useLocation().state?.message;
  const [notice, setNotice] = useState(fromModify ? { type: "success", text: fromModify } : null);

  const run = async (action) => {
    setBusy(true);
    setNotice(null);
    try {
      const { message } = await action();
      setNotice({ type: "success", text: message });
    } catch (err) {
      setNotice({ type: "error", text: errorsFrom(err).join(" ") });
    } finally {
      setBusy(false);
      reload(); // si falló, el estado de la reserva pudo cambiar
    }
  };

  const pickup = (rental) => {
    const charging = !rental.is_paid;
    if (charging && !window.confirm(`¿Ya cobraste ${formatMoney(rental.total_price)} en efectivo?`)) return;
    run(() => pickupReservation(rental.id, charging));
  };

  const cancel = (rental) => {
    if (!window.confirm(`¿Cancelar la reserva de ${rental.equipment.inventory_id}?`)) return;
    run(() => cancelRental(rental.id));
  };

  const columns = [
    { label: "Equipo", render: (r) => `${r.equipment.inventory_id} · ${r.equipment.name}` },
    { label: "Cliente", render: (r) => r.client },
    { label: "Desde", render: (r) => formatDateTime(r.start) },
    { label: "Hasta", render: (r) => formatDateTime(r.end) },
    { label: "Pago", render: (r) => <PaymentBadge rental={r} /> },
    {
      label: "",
      render: (r) => (
        <div className="row-actions">
          <button className="btn btn--primary" disabled={busy} onClick={() => pickup(r)}>
            {r.is_paid ? "Registrar recojo" : `Cobrar ${formatMoney(r.total_price)} y entregar`}
          </button>
          <Link className="btn btn--secondary" to={`/rentals/${r.id}/modify`}>Modificar</Link>
          <button className="btn btn--secondary" disabled={busy} onClick={() => cancel(r)}>Cancelar</button>
        </div>
      ),
    },
  ];

  return (
    <Layout title="Reservas por entregar">
      <OrderSelect value={order} onChange={setOrder} dateLabel="Más próximas" />
      {notice && <Alert type={notice.type}>{notice.text}</Alert>}
      {error && <Alert>{error}</Alert>}
      {loading && !data && <p className="list-message">Cargando reservas…</p>}
      {data && data.length === 0 && <p className="list-message">No hay reservas por entregar.</p>}
      {data && data.length > 0 && <DataTable columns={columns} rows={data} rowKey={(r) => r.id} />}
    </Layout>
  );
}
