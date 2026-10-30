import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import Layout from "../../components/Layout";
import { getCatalog } from "../../api/catalog";
import "./CatalogPage.css";

export default function CatalogPage() {
  const [catalog, setCatalog] = useState({ results: [], count: 0 });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [filters, setFilters] = useState({ q: "", free_from: "", free_to: "" });
  const [appliedFilters, setAppliedFilters] = useState({});

  useEffect(() => {
    setLoading(true);
    setError("");
    getCatalog(appliedFilters)
      .then(({ data }) => setCatalog(data))
      .catch((err) => setError(err.errors?.[0] || "No pudimos cargar el catálogo."))
      .finally(() => setLoading(false));
  }, [appliedFilters]);

  const updateFilter = (field) => (event) => {
    setFilters((current) => ({ ...current, [field]: event.target.value }));
  };

  const submitFilters = (event) => {
    event.preventDefault();
    setAppliedFilters(filters);
  };

  const clearFilters = () => {
    const empty = { q: "", free_from: "", free_to: "" };
    setFilters(empty);
    setAppliedFilters({});
  };

  return (
    <Layout title="Catálogo">
      <section className="catalog-hero">
        <div>
          <p className="eyebrow">SERGIOCORP · EQUIPOS PARA TU EVENTO</p>
          <h2>Encuentra lo que necesitas para celebrar.</h2>
          <p>Explora mesas y sillas disponibles, revisa el precio diario y reserva en pocos pasos.</p>
        </div>
        <div className="catalog-hero__stripes" />
      </section>

      <div className="catalog-heading">
        <div>
          <span className="eyebrow">CATÁLOGO</span>
          <h2>Equipos disponibles</h2>
        </div>
        {!loading && <span className="catalog-count">{catalog.count} equipos</span>}
      </div>

      <form className="catalog-filters" onSubmit={submitFilters}>
        <label>
          <span>Código o nombre:</span>
          <input value={filters.q} onChange={updateFilter("q")} placeholder="MES-00001 o Mesa redonda" />
        </label>
        <label>
          <span>Libre desde:</span>
          <input type="date" value={filters.free_from} onChange={updateFilter("free_from")} />
        </label>
        <label>
          <span>Libre hasta:</span>
          <input type="date" value={filters.free_to} onChange={updateFilter("free_to")} />
        </label>
        <div className="catalog-filters__actions">
          <button className="btn btn--primary" type="submit">Buscar</button>
          <button className="btn btn--secondary" type="button" onClick={clearFilters}>Limpiar</button>
        </div>
        <p className="catalog-filters__hint">Con las dos fechas ves solo los equipos libres desde las 18:00 del primer día hasta las 09:00 del último.</p>
      </form>

      {loading && <p className="catalog-message">Cargando equipos…</p>}
      {error && <p className="catalog-message catalog-message--error">{error}</p>}
      {!loading && !error && catalog.results.length === 0 && (
        <p className="catalog-message">No hay equipos disponibles por ahora.</p>
      )}

      <div className="catalog-grid">
        {catalog.results.map((equipment) => (
          <article className="catalog-card" key={equipment.inventory_id}>
            <div className="catalog-card__image">
              <img
                src={`/img/equipment/${equipment.inventory_id}.jpg`}
                alt={equipment.name}
                loading="lazy"
                onError={(e) => {
                  e.currentTarget.style.display = "none";
                }}
              />
              <span>PRÓXIMAMENTE</span>
            </div>
            <div className="catalog-card__body">
              <p className="catalog-card__code">{equipment.inventory_id}</p>
              <h3>{equipment.name}</h3>
              <p className="catalog-card__status">{equipment.status_label || "Disponible"}</p>
              <div className="catalog-card__footer">
                <strong>{equipment.daily_price} <small>/ día</small></strong>
                <Link className="btn btn--primary" to={`/equipment/${equipment.inventory_id}/rent`}>
                  Reservar
                </Link>
              </div>
            </div>
          </article>
        ))}
      </div>
    </Layout>
  );
}
