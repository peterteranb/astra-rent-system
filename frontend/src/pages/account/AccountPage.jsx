import { useState } from "react";
import Layout from "../../components/Layout";
import Alert from "../../components/Alert";
import Rejection from "../../components/Rejection";
import Field from "../../components/Field";
import { useAuth } from "../../auth/AuthContext";
import { updateAccount } from "../../api/auth";
import { errorsFrom } from "../../utils/friendlyErrors";
import { Link } from "react-router-dom";
import "./AccountPage.css";

export default function AccountPage() {
  const { user, refresh } = useAuth();
  const [form, setForm] = useState({
    first_name: user.first_name,
    last_name: user.last_name,
    email: user.email,
    phone: user.phone,
  });
  const [errors, setErrors] = useState([]);
  const [message, setMessage] = useState("");
  const [sending, setSending] = useState(false);

  const change = (field) => (e) =>
    setForm({ ...form, [field]: e.target.value });

  const submit = async (e) => {
    e.preventDefault();
    setErrors([]);
    setMessage("");
    setSending(true);
    try {
      await updateAccount(form);
      await refresh();
      setMessage("Listo, guardamos tus datos.");
    } catch (err) {
      setErrors(errorsFrom(err));
    } finally {
      setSending(false);
    }
  };

  return (
    <Layout title="Mi cuenta">
      <section className="card account">
        <dl className="account__fixed">
          <div>
            <dt>Usuario</dt>
            <dd>{user.username}</dd>
          </div>
          <div>
            <dt>Rol</dt>
            <dd>{user.role_name}</dd>
          </div>
        </dl>
        <p className="field__hint">El usuario y el rol no se cambian.</p>

        <form className="form" onSubmit={submit} noValidate>
          {message && <Alert type="success">{message}</Alert>}
          <Rejection title="Revisa estos datos:" errors={errors} />

          <Field
            id="first_name"
            label="Nombre"
            autoComplete="given-name"
            value={form.first_name}
            onChange={change("first_name")}
          />
          <Field
            id="last_name"
            label="Apellido"
            autoComplete="family-name"
            value={form.last_name}
            onChange={change("last_name")}
          />
          <Field
            id="email"
            label="Correo"
            type="email"
            autoComplete="email"
            value={form.email}
            onChange={change("email")}
          />
          <Field
            id="phone"
            label="Teléfono"
            type="tel"
            autoComplete="tel"
            hint="Solo números, de 7 a 15."
            value={form.phone}
            onChange={change("phone")}
          />

          <button className="btn btn--primary" type="submit" disabled={sending}>
            {sending ? "Guardando…" : "Guardar mis datos"}
          </button>

          <hr className="divider" />
          <Link className="btn btn--secondary" to="/account/password">
            Cambiar contraseña
          </Link>
        </form>
      </section>
    </Layout>
  );
}
