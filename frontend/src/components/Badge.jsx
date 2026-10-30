import "./Badge.css";
const TONES = { reserved: "info", rented: "warning", in_review: "warning", returned: "success", available: "success", paid: "success", cancelled: "error", in_repair: "error", retired: "error", pending: "error" };
export default function Badge({ tone, children }) { return <span className={`badge badge--${TONES[tone] ?? "neutral"}`}>{children}</span>; }
