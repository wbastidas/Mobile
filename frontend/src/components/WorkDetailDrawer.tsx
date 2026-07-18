import { useQuery } from "@tanstack/react-query";
import { dashboardApi, noveltiesApi } from "@/api/endpoints";
import { errorMessage } from "@/api/client";
import { ErrorBox, Loading, StatusBadge, typeLabel } from "@/components/ui";
import type { Work } from "@/types";

const ACTION_LABEL: Record<string, string> = {
  CREATE: "Creación",
  ASSIGN: "Asignación",
  SYNC_RECEIVE: "Sync recibida",
  SYNC_VERIFY: "Sync verificada",
  CONSOLIDATE: "Consolidación",
  REMOTE_DELETE_ORDER: "Orden borrado remoto",
  REMOTE_DELETE_CONFIRM: "Borrado remoto confirmado",
  UPDATE: "Actualización",
};

const RULE_LABEL: Record<string, string> = {
  required: "Campo obligatorio",
  domain: "Fuera de dominio",
  range: "Fuera de rango",
  min_photos: "Fotos insuficientes",
  requires_parent: "Falta elemento padre",
  requires_geometry: "Falta geometría",
};

/**
 * Panel de detalle de un trabajo: línea de tiempo (RF-WEB-06.4) y novedades de
 * calidad por elemento y por regla (RF-WEB-09.2).
 */
export default function WorkDetailDrawer({ work, onClose }: { work: Work; onClose: () => void }) {
  const timeline = useQuery({
    queryKey: ["timeline", work.id],
    queryFn: () => dashboardApi.timeline(work.id),
  });
  const novelties = useQuery({
    queryKey: ["novelties", work.id],
    queryFn: () => noveltiesApi.byWork(work.id),
  });

  return (
    <div
      style={{ position: "fixed", inset: 0, background: "rgba(15,23,42,0.5)", zIndex: 50 }}
      onClick={onClose}
    >
      <aside
        onClick={(e) => e.stopPropagation()}
        style={{
          position: "absolute",
          top: 0,
          right: 0,
          height: "100%",
          width: "min(560px, 100%)",
          background: "var(--surface)",
          boxShadow: "-8px 0 24px rgba(0,0,0,0.2)",
          overflowY: "auto",
          padding: "1.5rem",
        }}
      >
        <div className="row between" style={{ marginBottom: "0.5rem" }}>
          <h2 style={{ margin: 0 }}>{work.code}</h2>
          <button className="btn secondary sm" onClick={onClose}>
            ✕ Cerrar
          </button>
        </div>
        <p className="muted" style={{ marginTop: 0 }}>
          {work.title}
        </p>
        <div className="row" style={{ gap: "0.5rem", marginBottom: "1.25rem" }}>
          <StatusBadge status={work.status} />
          <span className="badge gray">{typeLabel(work.work_type)}</span>
          {work.validation_result === "WITH_ISSUES" && (
            <span className="badge amber">Con novedades</span>
          )}
        </div>

        <h3>Novedades de calidad</h3>
        {novelties.isLoading ? (
          <Loading />
        ) : novelties.error ? (
          <ErrorBox message={errorMessage(novelties.error)} />
        ) : novelties.data!.length === 0 ? (
          <p className="muted">Sin novedades de calidad registradas para este trabajo.</p>
        ) : (
          <div className="table-wrap" style={{ marginBottom: "1.5rem" }}>
            <table>
              <thead>
                <tr>
                  <th>Elemento</th>
                  <th>Campo</th>
                  <th>Regla</th>
                  <th>Esperado / actual</th>
                </tr>
              </thead>
              <tbody>
                {novelties.data!.map((n) => (
                  <tr key={n.id}>
                    <td>
                      <div>{n.element_type ?? "—"}</div>
                      <div className="muted" style={{ fontSize: "0.75rem" }}>
                        {n.element_guid ? `${n.element_guid.slice(0, 14)}…` : ""}
                      </div>
                    </td>
                    <td>{n.field ?? "—"}</td>
                    <td>
                      <span className="badge amber">{RULE_LABEL[n.rule_type] ?? n.rule_type}</span>
                    </td>
                    <td className="muted">
                      {n.expected ?? "—"}
                      {n.actual != null ? ` / ${n.actual}` : ""}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        <h3>Línea de tiempo</h3>
        {timeline.isLoading ? (
          <Loading />
        ) : timeline.error ? (
          <ErrorBox message={errorMessage(timeline.error)} />
        ) : timeline.data!.length === 0 ? (
          <p className="muted">Sin eventos registrados.</p>
        ) : (
          <ul style={{ paddingLeft: "1rem" }}>
            {timeline.data!.map((e, i) => (
              <li key={i} style={{ marginBottom: "0.5rem" }}>
                <strong>{ACTION_LABEL[e.action] ?? e.action}</strong>
                <div className="muted" style={{ fontSize: "0.8rem" }}>
                  {new Date(e.at).toLocaleString()}
                  {e.username ? ` · ${e.username}` : ""}
                </div>
              </li>
            ))}
          </ul>
        )}
      </aside>
    </div>
  );
}
