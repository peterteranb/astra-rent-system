import { useState } from "react";
import Layout from "../../components/Layout";
import Alert from "../../components/Alert";
import Rejection from "../../components/Rejection";
import Field from "../../components/Field";
import { createEquipment } from "../../api/manager";
import { errorsFrom } from "../../utils/friendlyErrors";
import "../account/AccountPage.css";

const EMPTY = { inventory_id: "", serial_number: "", name: "", value: "" };

export default function EquipmentFormPage() {
  const [form, setForm] = useState(EMPTY);
  const [errors, setErrors] = useState([]);
  const [message, setMessage] = useState("");
  const [sending, setSending] = useState(false);

  const change = (field) => (e) => setForm({ ...form, [field]: e.target.value });

  const submit = async (e) => {
    e.preventDefault();
    setErrors([]);
    setMessage("");
    setSending(true);
    try {
      const { message: registered } = await createEquipment(form);
      setMessage(registered);
      setForm(EMPTY);
    } catch (err) {
      setErrors(errorsFrom(err));
    } finally {
      setSending(false);
    }
  };

  return (
    <Layout title="Registrar equipo">
      <section className="card account">
        <form className="form" onSubmit={submit} noValidate>
          {message && <Alert type="success">{message}</Alert>}
          <Rejection title="Revisa estos datos:" errors={errors} />

          <Field id="inventory_id" label="Código" hint="3 letras, un guion y 5 números, por ejemplo MES-00021."
            value={form.inventory_id} onChange={change("inventory_id")} />
          <Field id="serial_number" label="Número de serie"
            value={form.serial_number} onChange={change("serial_number")} />
          <Field id="name" label="Nombre" value={form.name} onChange={change("name")} />
          <Field id="value" label="Valor de compra (Bs)" inputMode="decimal" hint="Por ejemplo 400.00."
            value={form.value} onChange={change("value")} />

          <button className="btn btn--primary" type="submit" disabled={sending}>
            {sending ? "Registrando…" : "Registrar equipo"}
          </button>
        </form>
      </section>
    </Layout>
  );
}
