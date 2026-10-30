export default function OrderSelect({ value, onChange, dateLabel }) {
  return <div className="field order-select"><label className="field__label" htmlFor="order">Ordenar por</label><div className="field__control"><select id="order" className="field__input" value={value} onChange={(e) => onChange(e.target.value)}><option value="">Más recientes</option><option value="date">{dateLabel}</option></select></div></div>;
}
