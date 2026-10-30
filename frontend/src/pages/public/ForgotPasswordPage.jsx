import { useState } from "react";
import { Link } from "react-router-dom";
import AuthLayout from "../../components/AuthLayout";
import Alert from "../../components/Alert";
import FormErrors from "../../components/FormErrors";
import Field from "../../components/Field";
import { requestPasswordReset } from "../../api/auth";
import { errorsFrom } from "../../utils/friendlyErrors";
export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [errors, setErrors] = useState([]);
  const [message, setMessage] = useState("");
  const [sending, setSending] = useState(false);
  const submit = async (e) => {
    e.preventDefault();
    setErrors([]);
    if (!email.trim()) {
      setErrors(["Escribe el correo de tu cuenta."]);
      return;
    }
    setSending(true);
    try {
      const { message: sent } = await requestPasswordReset(email.trim());
      setMessage(sent);
    } catch (err) {
      setErrors(errorsFrom(err));
    } finally {
      setSending(false);
    }
  };
  return (
    <AuthLayout
      heading="Recupera tu acceso."
      text="Te mandamos un enlace al correo para que crees una contraseña nueva."
    >
      <section className="card">
        <p className="eyebrow">RECUPERAR CONTRASEÑA</p>
        <h1 className="auth__title">¿Olvidaste tu contraseña?</h1>
        <p className="lead">
          Escribe tu correo y te enviamos un enlace para crear una nueva.
        </p>
        <form className="form" onSubmit={submit} noValidate>
          {message && <Alert type="success">{message}</Alert>}
          <FormErrors errors={errors} />
          <Field
            id="email"
            label="Correo electrónico"
            type="email"
            autoComplete="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
          <button className="btn btn--primary" type="submit" disabled={sending}>
            {sending ? "Enviando…" : "Enviar enlace"}
          </button>
          <hr className="divider" />
          <Link className="btn btn--secondary" to="/login">
            Volver a iniciar sesión
          </Link>
        </form>
      </section>
    </AuthLayout>
  );
}
