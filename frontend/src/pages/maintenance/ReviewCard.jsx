import { useState } from "react";
import Badge from "../../components/Badge";
import FormErrors from "../../components/FormErrors";
import { reviewEquipment } from "../../api/maintenance";
import { errorsFrom } from "../../utils/friendlyErrors";
import EquipmentImage from "../../components/EquipmentImage";

// La casilla de cobro solo aparece si el estado nuevo es reparación o baja
// y el equipo tiene una renta devuelta a quien cobrarle.
const DAMAGE_STATES = ["in_repair", "retired"];

export default function ReviewCard({ item, onSaved }) {
  const [status, setStatus] = useState(item.choices[0]?.value ?? "");
  const [comment, setComment] = useState("");
  const [charge, setCharge] = useState(false);
  const [sending, setSending] = useState(false);
  const [errors, setErrors] = useState([]);

  const showCharge =
    Boolean(item.last_client) && DAMAGE_STATES.includes(status);

  const submit = async (e) => {
    e.preventDefault();
    setErrors([]);
    setSending(true);
    try {
      const { message } = await reviewEquipment(item.inventory_id, {
        status,
        comment,
        charge_last_client: showCharge && charge, // siempre sin marcar por defecto
      });
      onSaved(message);
    } catch (err) {
      setErrors(errorsFrom(err));
      setSending(false);
    }
  };

  return (
    <li className="maint-item">
      <EquipmentImage
        inventoryId={item.inventory_id}
        name={item.name}
        className="maint-item__image"
      />
      <div className="maint-item__details">
        <div className="maint-item__head">
          <span className="maint-item__id">{item.inventory_id}</span>
          <span className="maint-item__name">{item.name}</span>
          <Badge tone={item.status}>{item.status_label}</Badge>
        </div>

        <form className="maint-form" onSubmit={submit} noValidate>
          <FormErrors errors={errors} />

          <div className="maint-form__row">
            <div className="field">
              <label
                className="field__label"
                htmlFor={`status-${item.inventory_id}`}
              >
                Nuevo estado
              </label>
              <div className="field__control">
                <select
                  id={`status-${item.inventory_id}`}
                  className="field__input"
                  value={status}
                  onChange={(e) => setStatus(e.target.value)}
                >
                  {item.choices.map(({ value, label }) => (
                    <option key={value} value={value}>
                      {label}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div className="field">
              <label
                className="field__label"
                htmlFor={`comment-${item.inventory_id}`}
              >
                Comentario (opcional)
              </label>
              <div className="field__control">
                <input
                  id={`comment-${item.inventory_id}`}
                  className="field__input"
                  value={comment}
                  onChange={(e) => setComment(e.target.value)}
                />
              </div>
            </div>

            <button
              className="btn btn--primary"
              type="submit"
              disabled={sending}
            >
              {sending ? "Guardando…" : "Guardar"}
            </button>
          </div>

          {showCharge && (
            <label className="maint-check">
              <input
                type="checkbox"
                checked={charge}
                onChange={(e) => setCharge(e.target.checked)}
              />
              {item.charge_label}
            </label>
          )}
        </form>
      </div>
    </li>
  );
}
