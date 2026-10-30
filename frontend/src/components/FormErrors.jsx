import Alert from "./Alert";

// Errores generales de un formulario: una frase sola, o una lista si son varias.
export default function FormErrors({ errors = [] }) {
  if (errors.length === 0) return null;
  if (errors.length === 1) return <Alert>{errors[0]}</Alert>;
  return <Alert items={errors} />;
}