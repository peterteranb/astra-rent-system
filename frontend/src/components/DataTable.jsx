import "./DataTable.css";

// columns = [{ label, render(row) }]; una columna con label "" es la de botones.
export default function DataTable({ columns, rows, rowKey }) {
  return (
    <table className="table">
      <thead>
        <tr>{columns.map((column, index) => <th key={index}>{column.label}</th>)}</tr>
      </thead>
      <tbody>
        {rows.map((row) => (
          <tr key={rowKey(row)}>
            {columns.map((column, index) => (
              <td
                key={index}
                data-label={column.label || undefined}
                className={column.label ? undefined : "table__actions"}
              >
                {column.render(row)}
              </td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  );
}
