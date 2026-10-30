import Alert from "./Alert";

// Rechazo con varias causas: el título dice qué no se hizo y la lista, todas las causas juntas.
export default function Rejection({ title, errors = [] }) {
  if (errors.length === 0) return null;
  return <Alert title={title} items={errors} />;
}