import { useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { useAuth, homePathFor } from "../../auth/AuthContext";
import { signUp } from "../../api/auth";
import Rejection from "../../components/Rejection";
import AuthLayout from "../../components/AuthLayout";
import Alert from "../../components/Alert";
import Field from "../../components/Field";

// "María Fernanda Rojas" -> nombre "María Fernanda", apellido "Rojas"
function splitName(fullName) {
  const parts = fullName.trim().split(/\s+/).filter(Boolean);
  if (parts.length < 2) return null;
  const cut = Math.ceil(parts.length / 2);
  return { first_name: parts.slice(0, cut).join(" "), last_name: parts.slice(cut).join(" ") };
}

export default function SignupPage() {
  const { user, loading } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({
    fullName: "", email: "", phone: "", password: "", confirmation: "",
  });
  const [accepted, setAccepted] = useState(false);
  const [errors, setErrors] = useState([]);
  const [sending, setSending] = useState(false);

  if (loading) return null;
  if (user) return <Navigate to={homePathFor(user.role)} replace />;

  const update = (field) => (e) => setForm({ ...form, [field]: e.target.value });

  const submit = async (e) => {
    e.preventDefault();
    setErrors([]);

    const name = splitName(form.fullName);
    if (!name) {
      setErrors(["Escribe tu nombre y tu apellido."]);
      return;
    }
    if (!accepted) {
      setErrors(["Para crear tu cuenta, acepta los términos de renta y la política de privacidad."]);
      return;
    }

    setSending(true);
    try {
      const email = form.email.trim().toLowerCase();
      const { message } = await signUp({
        ...name,
        email,
        phone: form.phone,
        username: email, // el correo sirve como usuario
        password: form.password,
        password_confirmation: form.confirmation,
      });
      navigate("/login", { state: { message } });
    } catch (err) {
      setErrors(errorsFrom(err));
      setSending(false);
    }
  };

  return (
    <AuthLayout
      heading="Crea tu cuenta para reservar."
      text="Consulta la disponibilidad de mesas y sillas y reserva equipos para tu evento."
    >
      <section className="card">
        <p className="eyebrow">REGISTRO DE CLIENTES</p>
        <h1 className="auth__title">Crear cuenta</h1>
        <p className="lead">Reserva equipos y sigue tus rentas desde un solo lugar.</p>

        <form className="form" onSubmit={submit} noValidate>
          <Rejection title="Revisa estos datos:" errors={errors} />
          {errors.length === 0 && (
            <Alert type="info">Crea tu cuenta de cliente. Todos los campos son obligatorios.</Alert>
          )}

          <Field id="fullName" label="Nombre completo" autoComplete="name"
            placeholder="María Fernanda Rojas" value={form.fullName} onChange={update("fullName")} />
          <Field id="email" label="Correo electrónico" type="email" autoComplete="email"
            placeholder="maria.rojas@gmail.com" value={form.email} onChange={update("email")} />
          <Field id="phone" label="Teléfono / WhatsApp" type="tel" autoComplete="tel"
            placeholder="+59174457552" hint="Solo números, de 7 a 15."
            value={form.phone} onChange={update("phone")} />
          <Field id="password" label="Contraseña" type="password" autoComplete="new-password"
            hint="Usa 8 caracteres o más, una mayúscula y un número."
            value={form.password} onChange={update("password")} />
          <Field id="confirmation" label="Confirmar contraseña" type="password" autoComplete="new-password"
            value={form.confirmation} onChange={update("confirmation")} />

          <label className="check">
            <input type="checkbox" checked={accepted} onChange={(e) => setAccepted(e.target.checked)} />
            Acepto los términos de renta y la política de privacidad de SergioCorp.
          </label>

          <button className="btn btn--primary" type="submit" disabled={sending}>
            {sending ? "Creando tu cuenta…" : "Crear mi cuenta"}
          </button>

          <hr className="divider" />
          <div className="auth__switch">
            <p>¿Ya tienes una cuenta?</p>
            <Link className="btn btn--secondary" to="/login">Iniciar sesión</Link>
          </div>
        </form>
      </section>
    </AuthLayout>
  );
}