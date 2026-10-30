import { useState } from "react";
import Layout from "../../components/Layout";
import Alert from "../../components/Alert";
import DataTable from "../../components/DataTable";
import { getStaffDebts, payDebt } from "../../api/staff";
import { errorsFrom } from "../../utils/friendlyErrors";
import { useLoader } from "../../utils/useLoader";
import { formatDateTime, formatMoney } from "../../utils/format";

export default function StaffDebtsPage() {
  const { data, loading, error, reload } = useLoader(getStaffDebts);
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState(null);

  const pay = async (debt) => {
    // El dinero se cobra en persona: se confirma antes de registrar.
    if (!window.confirm(`¿El cliente ya pagó ${formatMoney(debt.amount)}?`)) return;
    setBusy(true);
    setNotice(null);
    try {
      const { message } = await payDebt(debt.id);
      setNotice({ type: "success", text: message });
    } catch (err) {
      setNotice({ type: "error", text: errorsFrom(err).join(" ") });
    } finally {
      setBusy(false);
      reload(); // aunque falle, otro operador pudo haberla cobrado antes
    }
  };

  const columns = [
    { label: "Cliente", render: (d) => d.client },
    { label: "Equipo", render: (d) => d.equipment },
    { label: "Motivo", render: (d) => d.reason_label },
    { label: "Monto", render: (d) => formatMoney(d.amount) },
    { label: "Desde", render: (d) => formatDateTime(d.created_at) },
    {
      label: "",
      render: (d) => (
        <div className="row-actions">
          <button className="btn btn--primary" disabled={busy} onClick={() => pay(d)}>
            Registrar pago
          </button>
        </div>
      ),
    },
  ];

  return (
    <Layout title="Deudas pendientes">
      {notice && <Alert type={notice.type}>{notice.text}</Alert>}
      {error && <Alert>{error}</Alert>}
      {loading && !data && <p className="list-message">Cargando deudas…</p>}
      {data && data.debts.length === 0 && <p className="list-message">No hay deudas pendientes.</p>}

      {data && data.debts.length > 0 && (
        <>
          <section className="card totals">
            <h2 className="card__title">Total por cliente</h2>
            <ul>
              {data.totals.map((row) => (
                <li key={row.username}>
                  {row.first_name} {row.last_name} ({row.username}): <strong>{formatMoney(row.total)}</strong>
                </li>
              ))}
            </ul>
          </section>
          <DataTable columns={columns} rows={data.debts} rowKey={(d) => d.id} />
        </>
      )}
    </Layout>
  );
}