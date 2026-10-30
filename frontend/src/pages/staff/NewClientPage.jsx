import { useState } from "react";
import { useNavigate } from "react-router-dom";
import Layout from "../../components/Layout";
import Alert from "../../components/Alert";
import Rejection from "../../components/Rejection";
import Field from "../../components/Field";
import { createClient } from "../../api/staff";
import { errorsFrom } from "../../utils/friendlyErrors";
import "../account/AccountPage.css";
export default function NewClientPage() {
  const navigate = useNavigate();
  const [form, setForm] = useState({
    first_name: "",
    last_name: "",
    email: "",
    phone: "",
    username: "",
  });
  const [errors, setErrors] = useState([]);
  const [sending, setSending] = useState(false);
  const change = (f) => (e) => setForm({ ...form, [f]: e.target.value });
  const submit = async (e) => {
    e.preventDefault();
    setErrors([]);
    setSending(true);
    try {
      const { data, message } = await createClient(form);
      navigate(`/staff/walk-in?q=${encodeURIComponent(data.username)}`, {
        state: { text: message, type: data.email_sent ? "success" : "warning" },
      });
    } catch (err) {
      setErrors(errorsFrom(err));
      setSending(false);
    }
  };
  return (
    <Layout title="Nuevo cliente">
      <section className="card account">
        <form className="form" onSubmit={submit} noValidate>
          {errors.length ? (
            <Rejection title="Revisa estos datos:" errors={errors} />
          ) : (
            <Alert type="info">
              El cliente recibirá un correo para crear su contraseña.
            </Alert>
          )}
          <Field
            id="first_name"
            label="Nombre"
            value={form.first_name}
            onChange={change("first_name")}
          />
          <Field
            id="last_name"
            label="Apellido"
            value={form.last_name}
            onChange={change("last_name")}
          />
          <Field
            id="email"
            label="Correo"
            type="email"
            value={form.email}
            onChange={change("email")}
          />
          <Field
            id="phone"
            label="Teléfono"
            type="tel"
            hint="Solo números, de 7 a 15."
            value={form.phone}
            onChange={change("phone")}
          />
          <Field
            id="username"
            label="Usuario"
            hint="Con él inicia sesión."
            value={form.username}
            onChange={change("username")}
          />
          <button className="btn btn--primary" disabled={sending}>
            {sending ? "Registrando…" : "Registrar cliente"}
          </button>
        </form>
      </section>
    </Layout>
  );
}
