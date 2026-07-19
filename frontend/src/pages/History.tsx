import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { historyApi, worksApi } from "@/api/endpoints";
import { errorMessage } from "@/api/client";
import { ErrorBox, Loading, OperationBadge, PageHeader } from "@/components/ui";

/**
 * Histórico de cambios de campo por usuario y por trabajo (CREATE/UPDATE/DELETE).
 * Responde "¿qué hizo cada funcionario en cada trabajo?" (RF-WEB-07/08).
 */
export default function History() {
  const [workId, setWorkId] = useState("");

  const works = useQuery({ queryKey: ["works"], queryFn: () => worksApi.list() });
  const params = workId ? { work_id: workId } : undefined;
  const summary = useQuery({
    queryKey: ["history-summary", workId],
    queryFn: () => historyApi.summary(params),
  });
  const changes = useQuery({
    queryKey: ["history-changes", workId],
    queryFn: () => historyApi.changes(params),
  });

  return (
    <>
      <PageHeader
        title="Historial de cambios en campo"
        subtitle="Trazabilidad de todo lo que cada funcionario creó, modificó o eliminó en cada trabajo."
      />

      <div className="toolbar row">
        <div style={{ width: 320 }}>
          <select value={workId} onChange={(e) => setWorkId(e.target.value)} style={{ margin: 0 }}>
            <option value="">Todos los trabajos</option>
            {(works.data ?? []).map((w) => (
              <option key={w.id} value={w.id}>
                {w.code} — {w.title}
              </option>
            ))}
          </select>
        </div>
      </div>

      <h3>Resumen por funcionario</h3>
      {summary.isLoading ? (
        <Loading />
      ) : summary.error ? (
        <ErrorBox message={errorMessage(summary.error)} />
      ) : (
        <div className="table-wrap" style={{ marginBottom: "1.75rem" }}>
          <table>
            <thead>
              <tr>
                <th>Funcionario</th>
                <th>Creados</th>
                <th>Modificados</th>
                <th>Eliminados</th>
              </tr>
            </thead>
            <tbody>
              {summary.data!.map((r, i) => (
                <tr key={i}>
                  <td>{r.funcionario}</td>
                  <td>{r.CREATE ?? 0}</td>
                  <td>{r.UPDATE ?? 0}</td>
                  <td>{r.DELETE ?? 0}</td>
                </tr>
              ))}
              {summary.data!.length === 0 && (
                <tr>
                  <td colSpan={4} className="empty">Sin cambios registrados.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      <h3>Detalle de cambios</h3>
      {changes.isLoading ? (
        <Loading />
      ) : changes.error ? (
        <ErrorBox message={errorMessage(changes.error)} />
      ) : (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Fecha/hora</th>
                <th>Funcionario</th>
                <th>Trabajo</th>
                <th>Operación</th>
                <th>Elemento</th>
              </tr>
            </thead>
            <tbody>
              {changes.data!.map((c) => (
                <tr key={c.id}>
                  <td className="muted">{new Date(c.created_at).toLocaleString()}</td>
                  <td>{c.username}</td>
                  <td>{c.work_code}</td>
                  <td><OperationBadge operation={c.operation} /></td>
                  <td className="muted">
                    {c.element_type} · {c.element_guid.slice(0, 16)}…
                  </td>
                </tr>
              ))}
              {changes.data!.length === 0 && (
                <tr>
                  <td colSpan={5} className="empty">Sin cambios registrados.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </>
  );
}
