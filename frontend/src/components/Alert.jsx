export default function Alert({ type = "error", title, items = [], children }) {
  return (
    <div
      className={`alert alert--${type}`}
      role={type === "error" ? "alert" : "status"}
    >
      <svg
        width="18"
        height="18"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        aria-hidden="true"
        style={{ flex: "none" }}
      >
        <circle cx="12" cy="12" r="10" />
        <path d="M12 16v-4M12 8h.01" />
      </svg>
      <div>
        {title && <p className="alert__title">{title}</p>}
        {items.length > 0 && (
          <ul className="alert__list">
            {items.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        )}
        {children}
      </div>
    </div>
  );
}
