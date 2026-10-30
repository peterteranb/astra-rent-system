import { Link, useLocation } from "react-router-dom";
import Layout from "../../components/Layout";
import Alert from "../../components/Alert";
import Badge from "../../components/Badge";
import DataTable from "../../components/DataTable";
import { getStaffReturns } from "../../api/staff";
import { useLoader } from "../../utils/useLoader";
import { formatDateTime } from "../../utils/format";

export default function StaffReturnsPage() {
  const { data, loading, error } = useLoader(getStaffReturns);
  const message = useLocation().state?.message; // viene de la pantalla de devolución

  const columns = [
    { label: "Equipo", render: (r) => `${r.equipment.inventory_id} · ${r.equipment.name}` },
    { label: "Cliente", render: (r) => r.client },
    { label: "Estado", render: (r) => <Badge tone={r.status}>{r.status_label}</Badge> },
    { label: "Vence", render: (r) => formatDateTime(r.end) },
    {
      label: "",
      render: (r) => (
        <div className="row-actions">
          <Link className="btn btn--primary" to={`/staff/returns/${r.id}`}>Registrar devolución</Link>
        </div>
      ),
    },
  ];

  return (
    <Layout title="Devoluciones pendientes">
      {message && <Alert type="success">{message}</Alert>}
      {error && <Alert>{error}</Alert>}
      {loading && !data && <p className="list-message">Cargando devoluciones…</p>}
      {data && data.length === 0 && <p className="list-message">No hay devoluciones pendientes.</p>}
      {data && data.length > 0 && <DataTable columns={columns} rows={data} rowKey={(r) => r.id} />}
    </Layout>
  );
}