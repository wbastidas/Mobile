import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { buApi, devicesApi, worksApi } from "@/api/endpoints";
import { errorMessage } from "@/api/client";
import { useAuth } from "@/auth/AuthContext";
import { ErrorBox, Loading, PageHeader, StatusBadge, typeLabel } from "@/components/ui";
import type { WorkType } from "@/types";

export default function Works() {
  const qc = useQueryClient();
  const { isOperator } = useAuth();
  const [showCreate, setShowCreate] = useState(false);
  const [assigning, setAssigning] = useState<string | null>(null); // work id
  const [error, setError] = useState("");

  const works = useQuery({ queryKey: ["works"], queryFn: () => worksApi.list() });
  const devices = useQuery({ queryKey: ["devices"], queryFn: devicesApi.list });

  const assign = useMutation({
    mutationFn: ({ deviceId, workId }: { deviceId: string; workId: string }) =>
      worksApi.assign(deviceId, [workId]),
    onSuccess: () => {
      setAssigning(null);
      setError("");
      qc.invalidateQueries({ queryKey: ["works"] });
    },
    onError: (e) => setError(errorMessage(e)),
  });

  const remoteDelete = useMutation({
    mutationFn: ({ deviceId, workId }: { deviceId: string; workId: string }) =>
      worksApi.remoteDelete(deviceId, [workId]),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["works"] }),
    onError: (e) => setError(errorMessage(e)),
  });

  if (works.isLoading) return <Loading />;
  if (works.error) return <ErrorBox message={errorMessage(works.error)} />;

  return (
    <>
      <PageHeader
        title="Trabajos"
        subtitle="Asignación, monitoreo y borrado remoto. Un trabajo se asigna a un solo dispositivo a la vez (RN-01)."
        actions={
          isOperator && (
            <button className="btn" onClick={() => setShowCreate(true)}>
              + Nuevo trabajo
            </button>
          )
        }
      />

      {error && <ErrorBox message={error} />}

      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Código</th>
              <th>Título</th>
              <th>Tipo</th>
              <th>Estado</th>
              <th>Dispositivo</th>
              {isOperator && <th>Acciones</th>}
            </tr>
          </thead>
          <tbody>
            {works.data!.map((w) => {
              const dev = devices.data?.find((d) => d.id === w.device_id);
              return (
                <tr key={w.id}>
                  <td>{w.code}</td>
                  <td>{w.title}</td>
                  <td>{typeLabel(w.work_type)}</td>
                  <td>
                    <StatusBadge status={w.status} />
                  </td>
                  <td className="muted">{dev ? dev.alias : "—"}</td>
                  {isOperator && (
                    <td>
                      {!w.device_id ? (
                        assigning === w.id ? (
                          <AssignInline
                            devices={(devices.data ?? []).filter((d) => d.un_id === w.un_id && d.active)}
                            onCancel={() => setAssigning(null)}
                            onAssign={(deviceId) => assign.mutate({ deviceId, workId: w.id })}
                            busy={assign.isPending}
                          />
                        ) : (
                          <button className="btn sm" onClick={() => setAssigning(w.id)}>
                            Asignar
                          </button>
                        )
                      ) : (
                        <button
                          className="btn sm danger"
                          onClick={() =>
                            remoteDelete.mutate({ deviceId: w.device_id!, workId: w.id })
                          }
                        >
                          Borrado remoto
                        </button>
                      )}
                    </td>
                  )}
                </tr>
              );
            })}
            {works.data!.length === 0 && (
              <tr>
                <td colSpan={isOperator ? 6 : 5} className="empty">
                  No hay trabajos en su ámbito.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {showCreate && (
        <CreateWorkModal
          onClose={() => setShowCreate(false)}
          onCreated={() => {
            setShowCreate(false);
            qc.invalidateQueries({ queryKey: ["works"] });
          }}
        />
      )}
    </>
  );
}

function AssignInline({
  devices,
  onAssign,
  onCancel,
  busy,
}: {
  devices: { id: string; alias: string }[];
  onAssign: (deviceId: string) => void;
  onCancel: () => void;
  busy: boolean;
}) {
  const [deviceId, setDeviceId] = useState(devices[0]?.id ?? "");
  return (
    <div className="row" style={{ gap: "0.4rem" }}>
      <select value={deviceId} onChange={(e) => setDeviceId(e.target.value)} style={{ margin: 0, width: 160 }}>
        {devices.length === 0 && <option value="">Sin dispositivos</option>}
        {devices.map((d) => (
          <option key={d.id} value={d.id}>
            {d.alias}
          </option>
        ))}
      </select>
      <button className="btn sm" disabled={!deviceId || busy} onClick={() => onAssign(deviceId)}>
        OK
      </button>
      <button className="btn sm secondary" onClick={onCancel}>
        ✕
      </button>
    </div>
  );
}

function CreateWorkModal({ onClose, onCreated }: { onClose: () => void; onCreated: () => void }) {
  const bus = useQuery({ queryKey: ["business-units"], queryFn: buApi.list });
  const [error, setError] = useState("");
  const [form, setForm] = useState({
    code: "",
    title: "",
    work_type: "ORDEN_PUNTUAL" as WorkType,
    un_id: "",
  });
  const options = useMemo(() => bus.data ?? [], [bus.data]);

  const create = useMutation({
    mutationFn: () =>
      worksApi.create({
        code: form.code,
        title: form.title,
        work_type: form.work_type,
        un_id: form.un_id || options[0]?.id || "",
      }),
    onSuccess: onCreated,
    onError: (e) => setError(errorMessage(e)),
  });

  return (
    <div className="login-wrap" style={{ position: "fixed", inset: 0, background: "rgba(15,23,42,0.55)" }}>
      <div className="login-card" style={{ width: 420 }}>
        <h1>Nuevo trabajo</h1>
        <p className="sub">Complete los datos del trabajo a crear.</p>
        {error && <ErrorBox message={error} />}
        <label>Código</label>
        <input value={form.code} onChange={(e) => setForm({ ...form, code: e.target.value })} />
        <label>Título</label>
        <input value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} />
        <label>Tipo de trabajo</label>
        <select
          value={form.work_type}
          onChange={(e) => setForm({ ...form, work_type: e.target.value as WorkType })}
        >
          <option value="REVISION_RED">Revisión de red (sector)</option>
          <option value="ORDEN_PUNTUAL">Orden puntual</option>
          <option value="MANTENIMIENTO">Mantenimiento / proyecto</option>
        </select>
        <label>Unidad de Negocio</label>
        <select value={form.un_id} onChange={(e) => setForm({ ...form, un_id: e.target.value })}>
          {options.map((u) => (
            <option key={u.id} value={u.id}>
              {u.code} — {u.name}
            </option>
          ))}
        </select>
        <div className="row" style={{ marginTop: "0.5rem" }}>
          <button className="btn" disabled={create.isPending} onClick={() => create.mutate()}>
            Crear
          </button>
          <button className="btn secondary" onClick={onClose}>
            Cancelar
          </button>
        </div>
      </div>
    </div>
  );
}
