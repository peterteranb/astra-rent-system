import { useState } from "react";
import { Link } from "react-router-dom";
import Layout from "../../components/Layout";
import Alert from "../../components/Alert";
import FormErrors from "../../components/FormErrors";
import Field from "../../components/Field";
import { changePassword } from "../../api/auth";
import { errorsFrom } from "../../utils/friendlyErrors";
import "./AccountPage.css";

const EMPTY = { old_password: "", new_password1: "", new_password2: "" };
export default function ChangePasswordPage() {
  const [form, setForm] = useState(EMPTY); const [errors, setErrors] = useState([]); const [message, setMessage] = useState(""); const [sending, setSending] = useState(false);
  const change = (field) => (e) => setForm({ ...form, [field]: e.target.value });
  const submit = async (e) => { e.preventDefault(); setErrors([]); setMessage(""); setSending(true); try { const { message: saved } = await changePassword(form); setMessage(saved); setForm(EMPTY); } catch (err) { setErrors(errorsFrom(err)); } finally { setSending(false); } };
  return <Layout title="Cambiar contraseña"><section className="card account"><form className="form" onSubmit={submit} noValidate>{message && <Alert type="success">{message}</Alert>}<FormErrors errors={errors}/><Field id="old_password" label="Contraseña actual" type="password" autoComplete="current-password" value={form.old_password} onChange={change("old_password")}/><Field id="new_password1" label="Contraseña nueva" type="password" autoComplete="new-password" hint="Usa 8 caracteres o más, una mayúscula y un número." value={form.new_password1} onChange={change("new_password1")}/><Field id="new_password2" label="Repite la contraseña nueva" type="password" autoComplete="new-password" value={form.new_password2} onChange={change("new_password2")}/><button className="btn btn--primary" type="submit" disabled={sending}>{sending ? "Guardando…" : "Cambiar contraseña"}</button><Link className="btn btn--secondary" to="/account">Volver a mi cuenta</Link></form></section></Layout>;
}
