import { useState } from "react";
import { Link, Navigate, useLocation } from "react-router-dom";
import { useAuth, homePathFor } from "../../auth/AuthContext";
import { errorsFrom } from "../../utils/friendlyErrors";
import FormErrors from "../../components/FormErrors";
import AuthLayout from "../../components/AuthLayout";
import Alert from "../../components/Alert";
import Field from "../../components/Field";

export default function LoginPage() {
  const { user, loading, login } = useAuth();
  const location = useLocation();
  const [form, setForm] = useState({ username: "", password: "" });
  const [errors, setErrors] = useState([]);
  const [sending, setSending] = useState(false);

  if (loading) return null;
  if (user) return <Navigate to={homePathFor(user.role)} replace />;

  const update = (field) => (e) => setForm({ ...form, [field]: e.target.value });

  const submit = async (e) => {
    e.preventDefault();
    setErrors([]);
    if (!form.username.trim() || !form.password) {
      setErrors(["Escribe tu usuario y tu contraseña."]);
      return;
    }
    setSending(true);
    try {
      await login(form.username.trim(), form.password);
    } catch (err) {
      setErrors(errorsFrom(err));
      setSending(false);
    }
  };

  return (
    <AuthLayout
      heading="Bienvenido de nuevo."
      text="Consulta la disponibilidad de mesas y sillas y gestiona tus rentas."
    >
      <section className="card">
        <p className="eyebrow">ACCESO A TU CUENTA</p>
        <h1 className="auth__title">Iniciar sesión</h1>
        <p className="lead">Entra para consultar equipos y gestionar tus rentas.</p>

        <form className="form" onSubmit={submit} noValidate>
          {location.state?.message && <Alert type="success">{location.state.message}</Alert>}
          <FormErrors errors={errors} />

          <Field id="username" label="Usuario o correo" autoComplete="username"
            value={form.username} onChange={update("username")} />
          <Field id="password" label="Contraseña" type="password" autoComplete="current-password"
            value={form.password} onChange={update("password")} />

          <button className="btn btn--primary" type="submit" disabled={sending}>
            {sending ? "Iniciando sesión…" : "Iniciar sesión"}
          </button>

          <hr className="divider" />
          <div className="auth__switch">
            <p>¿Es tu primera vez en SergioCorp?</p>
            <Link className="btn btn--secondary" to="/signup">Crear una cuenta</Link>
          </div>
        </form>
      </section>
    </AuthLayout>
  );
}