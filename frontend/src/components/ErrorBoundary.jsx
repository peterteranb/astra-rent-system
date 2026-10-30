import { Component } from "react";
import ErrorPage from "./ErrorPage";
export default class ErrorBoundary extends Component { state = { failed: false }; static getDerivedStateFromError() { return { failed: true }; } componentDidCatch(error) { console.error(error); } render() { if (!this.state.failed) return this.props.children; return <ErrorPage plain code="500" label="ALGO SALIÓ MAL" title="Algo salió mal de nuestro lado" text="No es un error tuyo. Vuelve a intentarlo en unos minutos. Si sigue pasando, avísanos en la tienda." />; } }
