import { ApiError } from "../api/client";

export function errorsFrom(
  err,
  { usernameTaken = "Ese usuario ya está en uso. Elige otro." } = {},
) {
  if (!(err instanceof ApiError)) {
    return ["No pudimos conectarnos. Revisa tu internet e inténtalo otra vez."];
  }

  const rules = [
    [/^El usuario .* ya existe\.$/, usernameTaken],
    [
      /^El correo ya está registrado\.$/,
      "Ya existe una cuenta con este correo.",
    ],
    [
      /^El teléfono ya está registrado\.$/,
      "Ya existe una cuenta con este teléfono.",
    ],
    [
      /^El usuario, el correo o el teléfono ya están registrados\.$/,
      "Ya existe una cuenta con estos datos.",
    ],
    [
      /^El usuario solo puede tener letras.*$/,
      "El usuario solo puede tener letras, números y los signos @ . + - _",
    ],
    [/^Cliente: .*$/, "Elige un cliente de la lista."],
    [/^Equipo: .*$/, "Elige un equipo de la lista."],
    [/^(.*): Este campo es obligatorio\.$/, "Falta completar: $1."],
    [
      /^(.*): Introduzca una (?:fecha|hora) válida\.$/,
      "Revisa «$1»: no es válida.",
    ],
    [/^Falta el campo (.*)\.$/, "Falta completar: $1."],
    [
      /^La sesión de seguridad venció.*$/,
      "Pasó mucho tiempo. Recarga la página e inténtalo otra vez.",
    ],
  ];

  const texts = err.errors.map((message) => {
    for (const [pattern, text] of rules) {
      if (pattern.test(message)) return message.replace(pattern, text);
    }
    return message;
  });
  return [...new Set(texts)];
}
