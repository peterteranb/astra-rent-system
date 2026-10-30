import Badge from "./Badge";

// «Pagado (QR)», «Pagado (efectivo)» o «Pago pendiente»; vienen listos desde la API.
export default function PaymentBadge({ rental }) {
  return (
    <Badge tone={rental.is_paid ? "paid" : "pending"}>
      {rental.payment_label}
    </Badge>
  );
}
