import { useEffect, useState } from "react";
import { Link, useLocation, useSearchParams } from "react-router-dom";
import Layout from "../../components/Layout";
import Alert from "../../components/Alert";
import FormErrors from "../../components/FormErrors";
import Field from "../../components/Field";
import PeriodFields from "../../components/PeriodFields";
import { searchClients, createWalkInRental } from "../../api/staff";
import { getCatalog } from "../../api/catalog";
import { errorsFrom } from "../../utils/friendlyErrors";
import { formatMoney, PICKUP_FROM, RETURN_UNTIL } from "../../utils/format";
import "./WalkInRentalPage.css";

const EMPTY = {
  start_date: "",
  start_time: PICKUP_FROM,
  end_date: "",
  end_time: RETURN_UNTIL,
};

const name = (u) => [u.first_name, u.last_name].filter(Boolean).join(" ") || "sin nombre";

export default function WalkInRentalPage() {
  const [params] = useSearchParams();
  const state = useLocation().state;

  const [notice, setNotice] = useState(state ?? null);
  const [query, setQuery] = useState(params.get("q") || "");
  const [clients, setClients] = useState(null);
  const [client, setClient] = useState(null);
  const [eqQuery, setEqQuery] = useState("");
  const [equipmentList, setEquipmentList] = useState(null);
  const [equipment, setEquipment] = useState(null);
  const [period, setPeriod] = useState(EMPTY);
  const [errors, setErrors] = useState([]);
  const [error, setError] = useState("");

  const findClients = async () => {
    try {
      const { data } = await searchClients(query);
      setClients(data);
      if (data.length === 1) setClient(data[0]);
    } catch (e) {
      setError(errorsFrom(e)[0]);
    }
  };

  useEffect(() => {
    if (query) findClients();
  }, []);

  const findEquipment = async (e) => {
    e.preventDefault();
    try {
      const { data } = await getCatalog({ q: eqQuery, status: "available" });
      setEquipmentList(
        data.results.filter((x) => x.inventory_id.includes(eqQuery.toUpperCase()))
      );
    } catch (x) {
      setError(errorsFrom(x)[0]);
    }
  };

  const submit = async (e) => {
    e.preventDefault();
    setErrors([]);
    if (!client || !equipment) {
      return setErrors(["Elige un cliente y un equipo."]);
    }
    try {
      const { message } = await createWalkInRental({
        client: client.id,
        equipment: equipment.inventory_id,
        ...period,
      });
      setNotice({ type: "success", text: message });
      setEquipment(null);
      setEquipmentList(null);
    } catch (x) {
      setErrors(errorsFrom(x));
    }
  };

  return (
    <Layout title="Renta en tienda">
      <div className="walkin">
        {notice && <Alert type={notice.type}>{notice.text}</Alert>}

        <section className="card">
          <h2>Cliente</h2>
          <form
            className="search-row"
            onSubmit={(e) => {
              e.preventDefault();
              findClients();
            }}
          >
            <Field
              id="client"
              label="Buscar cliente"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
            <button className="btn btn--primary">Buscar</button>
          </form>

          {error && <p>{error}</p>}

          {clients?.map((c) => (
            <label className="pick-item" key={c.id}>
              <input
                type="radio"
                checked={client?.id === c.id}
                onChange={() => setClient(c)}
              />
              {c.username} · {name(c)}
            </label>
          ))}

          {clients?.length === 0 && (
            <p>
              No encontrado.{" "}
              <Link to="/staff/clients/new">Registrar cliente nuevo</Link>
            </p>
          )}
        </section>

        <section className="card">
          <h2>2. Equipo</h2>
          <form className="search-row" onSubmit={findEquipment}>
            <Field
              id="equipment"
                label={
                    <>
                      Buscar por código
                      <br />
                      <small style={{ fontWeight: "normal", opacity: 0.8 }}>
                        MES para mesas, SIL para sillas y CMB para combos
                      </small>
                    </>
                  }
              value={eqQuery}
              onChange={(e) => setEqQuery(e.target.value)}
            />
            <button className="btn btn--primary">Buscar</button>
          </form>

          {equipmentList?.map((x) => (
            <label className="pick-item" key={x.inventory_id}>
              <input
                type="radio"
                checked={equipment?.inventory_id === x.inventory_id}
                onChange={() => setEquipment(x)}
              />
              {x.inventory_id} · {x.name} · {formatMoney(x.daily_price)}
            </label>
          ))}
        </section>

        <form className="card form" onSubmit={submit}>
          <h2>3. Fechas</h2>
          <Alert type="info">
            Recojo desde {PICKUP_FROM}; devolución hasta {RETURN_UNTIL}.
          </Alert>
          <FormErrors errors={errors} />
          <PeriodFields
            values={period}
            onChange={(f) => (e) =>
              setPeriod({ ...period, [f]: e.target.value })}
          />
          <button className="btn btn--primary">Registrar renta</button>
        </form>
      </div>
    </Layout>
  );
}