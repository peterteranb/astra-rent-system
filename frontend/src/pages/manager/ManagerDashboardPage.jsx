import Layout from "../../components/Layout";
import Alert from "../../components/Alert";
import { getManagerDashboard } from "../../api/manager";
import { DJANGO_ADMIN } from "../../utils/djangoAdmin";
import { useLoader } from "../../utils/useLoader";
import { formatDateTime, formatMoney } from "../../utils/format";
import "./ManagerDashboardPage.css";
const short = (iso) => formatDateTime(iso).replace(/\/\d{4}/, "");
function DashboardCard({ count, title, adminPath, total, rows, children }) {
  return (
    <section className="card dash__card">
      <div className="dash__head">
        <h2 className="dash__title">{title}</h2>
        <span className="dash__count">{count}</span>
      </div>
      {rows.length ? (
        <ul className="dash__list">{children}</ul>
      ) : (
        <p className="dash__empty">Nada por aquí.</p>
      )}
      {total > rows.length && (
        <p className="dash__more">
          Mostrando {rows.length} de {total}.
        </p>
      )}
      <a className="dash__link" href={`${DJANGO_ADMIN}${adminPath}`}>
        Ver en el admin
      </a>
    </section>
  );
}
function RentalsCard({ title, list, situation }) {
  return (
    <DashboardCard
      count={list.total}
      title={title}
      total={list.total}
      rows={list.rows}
      adminPath={`rentals/rental/?situacion=${situation}`}
    >
      {list.rows.map((r) => (
        <li key={r.id}>
          {r.equipment.inventory_id} · {r.client} · {short(r.start)} a{" "}
          {short(r.end)}
        </li>
      ))}
    </DashboardCard>
  );
}
export default function ManagerDashboardPage() {
  const { data, loading, error, reload } = useLoader(getManagerDashboard);
  return (
    <Layout title="Panel del responsable">
      {error && <Alert>{error}</Alert>}
      {loading && !data && <p className="list-message">Cargando panel…</p>}
      {data && (
        <>
          <div className="dash__toolbar">
            <button
              className="btn btn--secondary"
              onClick={reload}
              disabled={loading}
            >
              {loading ? "Actualizando…" : "Actualizar"}
            </button>
          </div>
          <div className="dash">
            <RentalsCard
              title="Rentas activas"
              list={data.active}
              situation="activas"
            />
            <RentalsCard
              title="Rentas vencidas"
              list={data.overdue}
              situation="vencidas"
            />
            <RentalsCard
              title="Reservas de hoy"
              list={data.today}
              situation="hoy"
            />
            <RentalsCard
              title="Reservas con pago pendiente"
              list={data.pending_payment}
              situation="pago_pendiente"
            />
            <DashboardCard
              count={data.to_review.total}
              title="Equipos en revisión o reparación"
              total={data.to_review.total}
              rows={data.to_review.rows}
              adminPath="rentals/equipment/?status__in=in_review,in_repair"
            >
              {data.to_review.rows.map((i) => (
                <li key={i.inventory_id}>
                  {i.inventory_id} · {i.name} · {i.status_label}
                </li>
              ))}
            </DashboardCard>
            <DashboardCard
              count={formatMoney(data.debt_total)}
              title="Deudas pendientes"
              total={data.debts_by_client.total}
              rows={data.debts_by_client.rows}
              adminPath="rentals/debt/?pagada=no"
            >
              {data.debts_by_client.rows.map((r) => (
                <li key={r.username}>
                  <a
                    href={`${DJANGO_ADMIN}rentals/debt/?pagada=no&q=${encodeURIComponent(r.username)}`}
                  >
                    {r.username}
                  </a>{" "}
                  · {formatMoney(r.total)}
                </li>
              ))}
            </DashboardCard>
          </div>
        </>
      )}
    </Layout>
  );
}
