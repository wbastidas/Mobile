import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { auditApi } from "@/api/endpoints";
import { errorMessage } from "@/api/client";
import { ErrorBox, Loading, PageHeader } from "@/components/ui";

const ACTION_LABEL: Record<string, string> = {
  CREATE: "Creación",
  UPDATE: "Actualización",
  DELETE: "Borrado",
  LOGIN: "Ingreso",
  LOGIN_FAILED: "Ingreso fallido",
  ASSIGN: "Asignación",
  REMOTE_DELETE_ORDER: "Orden borrado remoto",
  REMOTE_DELETE_CONFIRM: "Borrado remoto confirmado",
  SYNC_RECEIVE: "Sync recibida",
  SYNC_VERIFY: "Sync verificada",
  CONSOLIDATE: "Consolidación",
  QUALITY_PARAMS_UPLOAD: "Carga params calidad",
};

export default function Audit() {
  const [action, setAction] = useState("");
  const audit = useQuery({
    queryKey: ["audit", action],
    queryFn: () => auditApi.list(action ? { action } : undefined),
  });

  return (
    <>
      <PageHeader
        title="Auditoría"
        subtitle="Registro inmutable de acciones (append-only), respetando la segregación de UN (RF-WEB-08)."
      />

      <div className="toolbar row">
        <div style={{ width: 240 }}>
          <select value={action} onChange={(e) => setAction(e.target.value)} style={{ margin: 0 }}>
            <option value="">Todas las acciones</option>
            {Object.entries(ACTION_LABEL).map(([k, v]) => (
              <option key={k} value={k}>
                {v}
              </option>
            ))}
          </select>
        </div>
      </div>

      {audit.isLoading ? (
        <Loading />
      ) : audit.error ? (
        <ErrorBox message={errorMessage(audit.error)} />
      ) : (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Fecha/hora</th>
                <th>Usuario</th>
                <th>Rol</th>
                <th>Acción</th>
                <th>Entidad</th>
                <th>IP</th>
              </tr>
            </thead>
            <tbody>
              {audit.data!.map((a) => (
                <tr key={a.id}>
                  <td className="muted">{new Date(a.created_at).toLocaleString()}</td>
                  <td>{a.username ?? "—"}</td>
                  <td>{a.role ?? "—"}</td>
                  <td>{ACTION_LABEL[a.action] ?? a.action}</td>
                  <td className="muted">
                    {a.entity_type ? `${a.entity_type}` : "—"}
                  </td>
                  <td className="muted">{a.ip_address ?? "—"}</td>
                </tr>
              ))}
              {audit.data!.length === 0 && (
                <tr>
                  <td colSpan={6} className="empty">
                    Sin registros de auditoría.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </>
  );
}
