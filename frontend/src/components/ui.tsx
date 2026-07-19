import type { ReactNode } from "react";
import type { WorkStatus } from "@/types";

export function PageHeader({ title, subtitle, actions }: { title: string; subtitle?: string; actions?: ReactNode }) {
  return (
    <div className="row between" style={{ marginBottom: "1.25rem" }}>
      <div>
        <h1 className="page-title">{title}</h1>
        {subtitle && <p className="page-sub">{subtitle}</p>}
      </div>
      {actions}
    </div>
  );
}

const STATUS_STYLE: Record<WorkStatus, { cls: string; label: string }> = {
  CREATED: { cls: "gray", label: "Creado" },
  ASSIGNED: { cls: "blue", label: "Asignado" },
  DOWNLOADED: { cls: "blue", label: "Descargado" },
  IN_PROGRESS: { cls: "amber", label: "En ejecución" },
  SYNCING: { cls: "amber", label: "Sincronizando" },
  SYNCED: { cls: "green", label: "Sincronizado" },
  WITH_ISSUES: { cls: "amber", label: "Con novedades" },
  COMPLETED: { cls: "green", label: "Terminado" },
  SYNC_PENDING: { cls: "red", label: "Sync pendiente" },
};

export function StatusBadge({ status }: { status: WorkStatus }) {
  const s = STATUS_STYLE[status] ?? { cls: "gray", label: status };
  return <span className={`badge ${s.cls}`}>{s.label}</span>;
}

const TYPE_LABEL: Record<string, string> = {
  REVISION_RED: "Revisión de red",
  ORDEN_PUNTUAL: "Orden puntual",
  MANTENIMIENTO: "Mantenimiento",
};
export function typeLabel(t: string): string {
  return TYPE_LABEL[t] ?? t;
}

const BATCH_STYLE: Record<string, { cls: string; label: string }> = {
  PENDING_REVIEW: { cls: "gray", label: "En revisión" },
  QUEUED: { cls: "blue", label: "En cola" },
  PROCESSING: { cls: "amber", label: "Procesando" },
  LOADED: { cls: "green", label: "Cargado" },
  FAILED: { cls: "red", label: "Falló" },
  ROLLED_BACK: { cls: "gray", label: "Revertido" },
};
export function BatchStatusBadge({ status }: { status: string }) {
  const s = BATCH_STYLE[status] ?? { cls: "gray", label: status };
  return <span className={`badge ${s.cls}`}>{s.label}</span>;
}

const OP_STYLE: Record<string, { cls: string; label: string }> = {
  CREATE: { cls: "green", label: "Crear" },
  UPDATE: { cls: "blue", label: "Modificar" },
  DELETE: { cls: "red", label: "Eliminar" },
};
export function OperationBadge({ operation }: { operation: string }) {
  const s = OP_STYLE[operation] ?? { cls: "gray", label: operation };
  return <span className={`badge ${s.cls}`}>{s.label}</span>;
}

export function Loading() {
  return (
    <div className="loading" role="status" aria-live="polite">
      <span className="spinner" aria-hidden="true" />
      Cargando…
    </div>
  );
}

export function ErrorBox({ message }: { message: string }) {
  return <div className="error">⚠ {message}</div>;
}
