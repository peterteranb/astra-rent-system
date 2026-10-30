import Field from "./Field";
import { PICKUP_FROM, RETURN_UNTIL } from "../utils/format";
import "./PeriodFields.css";

// values = { start_date, start_time, end_date, end_time }; onChange("start_date") devuelve el manejador.
export default function PeriodFields({ values, onChange }) {
  return (
    <div className="rental-dates">
      <fieldset className="rental-dates__group">
        <legend className="rental-dates__legend">Recojo</legend>
        <Field
          id="start_date"
          label="Fecha de recojo"
          type="date"
          value={values.start_date}
          onChange={onChange("start_date")}
        />
        <Field
          id="start_time"
          label="Hora de recojo"
          type="time"
          hint={`Desde las ${PICKUP_FROM}`}
          value={values.start_time}
          onChange={onChange("start_time")}
        />
      </fieldset>

      <fieldset className="rental-dates__group">
        <legend className="rental-dates__legend">Devolución</legend>
        <Field
          id="end_date"
          label="Fecha de devolución"
          type="date"
          value={values.end_date}
          onChange={onChange("end_date")}
        />
        <Field
          id="end_time"
          label="Hora de devolución"
          type="time"
          hint={`Hasta las ${RETURN_UNTIL}`}
          value={values.end_time}
          onChange={onChange("end_time")}
        />
      </fieldset>
    </div>
  );
}
