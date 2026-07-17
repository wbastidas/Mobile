import { useQuery } from "@tanstack/react-query";
import { dashboardApi } from "@/api/endpoints";
import { errorMessage } from "@/api/client";
import { ErrorBox, Loading, PageHeader, StatusBadge, typeLabel } from "@/components/ui";
import type { WorkStatus } from "@/types";

export default function Dashboard() {
  const summary = useQuery({ queryKey: ["summary"], queryFn: dashboardApi.summary });
  const active = useQuery({ queryKey: ["map", "active"], queryFn: () => dashboardApi.map(false) });

  if (summary.isLoading) return <Loading />;
  if (summary.error) return <ErrorBox message={errorMessage(summary.error)} />;

  const s = summary.data!;
  return (
    <>
      <PageHeader
        title="Dashboard"
        subtitle="Panorama de trabajos según su ámbito (Matriz / Unidad de Negocio)."
      />

      <div className="grid cols-4" style={{ marginBottom: "1.5rem" }}>
        <div className="card stat">
          <div className="label">Total trabajos</div>
          <div className="value">{s.total}</div>
        </div>
        <div className="card stat">
          <div className="label">Activos</div>
          <div className="value" style={{ color: "var(--primary)" }}>
            {s.active}
          </div>
        </div>
        <div className="card stat">
          <div className="label">Terminados</div>
          <div className="value" style={{ color: "var(--success)" }}>
            {(s.by_status["COMPLETED"] ?? 0) + (s.by_status["WITH_ISSUES"] ?? 0)}
          </div>
        </div>
        <div className="card stat">
          <div className="label">Sync pendiente</div>
          <div className="value" style={{ color: "var(--danger)" }}>
            {s.by_status["SYNC_PENDING"] ?? 0}
          </div>
        </div>
      </div>

      <div className="grid cols-2" style={{ marginBottom: "1.5rem" }}>
        <div className="card">
          <h3 style={{ marginTop: 0 }}>Por estado</h3>
          {Object.entries(s.by_status).map(([k, v]) => (
            <div className="row between" key={k} style={{ padding: "0.35rem 0" }}>
              <StatusBadge status={k as WorkStatus} />
              <strong>{v}</strong>
            </div>
          ))}
          {Object.keys(s.by_status).length === 0 && <div className="muted">Sin datos.</div>}
        </div>
        <div className="card">
          <h3 style={{ marginTop: 0 }}>Por tipo de trabajo</h3>
          {Object.entries(s.by_type).map(([k, v]) => (
            <div className="row between" key={k} style={{ padding: "0.35rem 0" }}>
              <span>{typeLabel(k)}</span>
              <strong>{v}</strong>
            </div>
          ))}
          {Object.keys(s.by_type).length === 0 && <div className="muted">Sin datos.</div>}
        </div>
      </div>

      <h3>Trabajos activos en el mapa</h3>
      <p className="page-sub">
        Ubicación / extensión de cada trabajo activo. La vista de mapa interactiva
        se integrará con la capa geográfica (GeoJSON de sector disponible por trabajo).
      </p>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Código</th>
              <th>Título</th>
              <th>Tipo</th>
              <th>Estado</th>
              <th>Geometría</th>
            </tr>
          </thead>
          <tbody>
            {(active.data ?? []).map((w) => (
              <tr key={w.id}>
                <td>{w.code}</td>
                <td>{w.title}</td>
                <td>{typeLabel(w.work_type)}</td>
                <td>
                  <StatusBadge status={w.status} />
                </td>
                <td className="muted">{w.sector_geojson ? "Polígono de sector" : "—"}</td>
              </tr>
            ))}
            {(active.data ?? []).length === 0 && (
              <tr>
                <td colSpan={5} className="empty">
                  No hay trabajos activos.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </>
  );
}
