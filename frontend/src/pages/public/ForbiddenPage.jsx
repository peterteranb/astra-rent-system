import ErrorPage from "../../components/ErrorPage";
export default function ForbiddenPage() {
  return (
    <ErrorPage
      code="403"
      label="SIN PERMISO"
      title="No tienes permiso para ver esta página"
      text="Esta página es para otro tipo de usuario. Si necesitas entrar, cierra sesión e ingresa con la cuenta que corresponde."
    />
  );
}
