import { ApiError } from "../api/client";

const REPLACEMENTS = [
  [/^El usuario .* ya existe\.$/, "Ya existe una cuenta con este correo."],
  [/^El correo ya está registrado\.$/, "Ya existe una cuenta con este correo."],
  [/^El teléfono ya está registrado\.$/, "Ya existe una cuenta con este teléfono."],
  [/^El usuario, el correo o el teléfono ya están registrados\.$/, "Ya existe una cuenta con estos datos."],
  [/^El usuario solo puede tener letras.*$/, "El correo tiene caracteres que no podemos aceptar."],
  [/^Falta el campo (.*)\.$/, "Falta completar: $1."],
  [/^La sesión de seguridad venció.*$/, "Pasó mucho tiempo. Recarga la página e inténtalo otra vez."],
];

export function errorsFrom(err) {
  if (!(err instanceof ApiError)) {
    return ["No pudimos conectarnos. Revisa tu internet e inténtalo otra vez."];
  }
  const texts = err.errors.map((message) => {
    for (const [pattern, text] of REPLACEMENTS) {
      if (pattern.test(message)) return message.replace(pattern, text);
    }
    return message;
  });
  return [...new Set(texts)];
}