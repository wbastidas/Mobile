import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { gisApi } from "@/api/endpoints";
import { errorMessage } from "@/api/client";
import { useAuth } from "@/auth/AuthContext";
import {
  BatchStatusBadge,
  ErrorBox,
  Loading,
  OperationBadge,
  PageHeader,
} from "@/components/ui";

/**
 * Consolidación hacia ArcSDE/Oracle (§7): revisión y aprobación de lotes.
 * Los lotes aprobados se cargan de a uno por la cola de edición secuencial.
 */
export default function Consolidation() {
  const qc = useQueryClient();
  const { isOperator } = useAuth();
  const [statusFilter, setStatusFilter] = useState("");
  const [openId, setOpenId] = useState<string | null>(null);

  const batches = useQuery({
    queryKey: ["staging", statusFilter],
    queryFn: () => gisApi.batches(statusFilter ? { status_filter: statusFilter } : undefined),
    refetchInterval: 4000, // refleja el avance de la cola casi en vivo
  });

  if (batches.isLoading) return <Loading />;
  if (batches.error) return <ErrorBox message={errorMessage(batches.error)} />;

  return (
    <>
      <PageHeader
        title="Consolidación (ArcSDE/Oracle)"
        subtitle="Revisión y aprobación de lotes de cambios verificados. Los aprobados se cargan de a uno por la cola de edición (RN-11, §7.4)."
      />

      <div className="toolbar row">
        <div style={{ width: 240 }}>
          <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)} style={{ margin: 0 }}>
            <option value="">Todos los estados</option>
            <option value="PENDING_REVIEW">En revisión</option>
            <option value="QUEUED">En cola</option>
            <option value="PROCESSING">Procesando</option>
            <option value="LOADED">Cargado</option>
            <option value="FAILED">Falló</option>
            <option value="ROLLED_BACK">Revertido</option>
          </select>
        </div>
      </div>

      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>UN</th>
              <th>Elementos</th>
              <th>Estado</th>
              <th>Orden cola</th>
              <th>Creado</th>
              <th>Detalle</th>
            </tr>
          </thead>
          <tbody>
            {batches.data!.map((b) => (
              <tr key={b.id}>
                <td>{b.un_code}</td>
                <td>{b.element_count}</td>
                <td>
                  <BatchStatusBadge status={b.status} />
                  {b.error && (
                    <div className="muted" style={{ fontSize: "0.72rem", color: "var(--danger)" }}>
                      {b.error}
                    </div>
                  )}
                </td>
                <td className="muted">{b.queue_seq ?? "—"}</td>
                <td className="muted">{new Date(b.created_at).toLocaleString()}</td>
                <td>
                  <button className="btn secondary sm" onClick={() => setOpenId(b.id)}>
                    Ver
                  </button>
                </td>
              </tr>
            ))}
            {batches.data!.length === 0 && (
              <tr>
                <td colSpan={6} className="empty">
                  No hay lotes de consolidación en su ámbito.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {openId && (
        <BatchDrawer
          batchId={openId}
          canDecide={isOperator}
          onClose={() => setOpenId(null)}
          onDecided={() => {
            setOpenId(null);
            qc.invalidateQueries({ queryKey: ["staging"] });
          }}
        />
      )}
    </>
  );
}

function BatchDrawer({
  batchId,
  canDecide,
  onClose,
  onDecided,
}: {
  batchId: string;
  canDecide: boolean;
  onClose: () => void;
  onDecided: () => void;
}) {
  const [error, setError] = useState("");
  const batch = useQuery({ queryKey: ["staging-detail", batchId], queryFn: () => gisApi.batch(batchId) });

  const approve = useMutation({
    mutationFn: () => gisApi.approve(batchId),
    onSuccess: onDecided,
    onError: (e) => setError(errorMessage(e)),
  });
  const rollback = useMutation({
    mutationFn: () => gisApi.rollback(batchId),
    onSuccess: onDecided,
    onError: (e) => setError(errorMessage(e)),
  });

  const decidable = batch.data?.status === "PENDING_REVIEW" || batch.data?.status === "FAILED";

  return (
    <div
      style={{ position: "fixed", inset: 0, background: "rgba(15,23,42,0.5)", zIndex: 50 }}
      onClick={onClose}
    >
      <aside
        onClick={(e) => e.stopPropagation()}
        style={{
          position: "absolute", top: 0, right: 0, height: "100%", width: "min(620px, 100%)",
          background: "var(--surface)", boxShadow: "-8px 0 24px rgba(0,0,0,0.2)",
          overflowY: "auto", padding: "1.5rem",
        }}
      >
        <div className="row between" style={{ marginBottom: "0.75rem" }}>
          <h2 style={{ margin: 0 }}>Lote de consolidación</h2>
          <button className="btn secondary sm" onClick={onClose}>✕ Cerrar</button>
        </div>

        {batch.isLoading ? (
          <Loading />
        ) : batch.error ? (
          <ErrorBox message={errorMessage(batch.error)} />
        ) : (
          <>
            <div className="row" style={{ gap: "0.5rem", marginBottom: "1rem" }}>
              <BatchStatusBadge status={batch.data!.status} />
              <span className="badge gray">{batch.data!.un_code}</span>
              <span className="muted">{batch.data!.element_count} elementos</span>
            </div>
            {error && <ErrorBox message={error} />}

            {canDecide && decidable && (
              <div className="row" style={{ marginBottom: "1.25rem" }}>
                <button className="btn" disabled={approve.isPending} onClick={() => approve.mutate()}>
                  Aprobar y cargar
                </button>
                <button className="btn danger" disabled={rollback.isPending} onClick={() => rollback.mutate()}>
                  Revertir
                </button>
              </div>
            )}

            <h3>Cambios a aplicar</h3>
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Operación</th>
                    <th>Tipo</th>
                    <th>GUID</th>
                    <th>Padre</th>
                  </tr>
                </thead>
                <tbody>
                  {batch.data!.elements.map((e) => (
                    <tr key={e.guid + e.operation}>
                      <td><OperationBadge operation={e.operation} /></td>
                      <td>{e.element_type}</td>
                      <td className="muted">{e.guid}</td>
                      <td className="muted">{e.parent_guid ?? "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        )}
      </aside>
    </div>
  );
}
