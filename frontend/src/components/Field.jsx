import { useState } from "react";

export default function Field({
  id,
  label,
  type = "text",
  hint,
  ...inputProps
}) {
  const [visible, setVisible] = useState(false);
  const isPassword = type === "password";

  return (
    <div className="field">
      <label className="field__label" htmlFor={id}>
        {label}
      </label>
      <div className="field__control">
        <input
          id={id}
          className="field__input"
          type={isPassword && visible ? "text" : type}
          {...inputProps}
        />
        {isPassword && (
          <button
            type="button"
            className="field__toggle"
            onClick={() => setVisible(!visible)}
            aria-label={visible ? "Ocultar contraseña" : "Mostrar contraseña"}
          >
            <svg
              width="20"
              height="20"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              aria-hidden="true"
            >
              <path d="M1 12s4-7 11-7 11 7 11 7-4 7-11 7S1 12 1 12z" />
              <circle cx="12" cy="12" r="3" />
              {visible && <path d="M3 3l18 18" />}
            </svg>
          </button>
        )}
      </div>
      {hint && <p className="field__hint">{hint}</p>}
    </div>
  );
}
