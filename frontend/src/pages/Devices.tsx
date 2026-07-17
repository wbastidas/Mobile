import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { buApi, devicesApi } from "@/api/endpoints";
import { errorMessage } from "@/api/client";
import { useAuth } from "@/auth/AuthContext";
import { ErrorBox, Loading, PageHeader } from "@/components/ui";

export default function Devices() {
  const qc = useQueryClient();
  const { isOperator } = useAuth();
  const [error, setError] = useState("");
  const [form, setForm] = useState({ device_uid: "", alias: "", un_id: "" });

  const devices = useQuery({ queryKey: ["devices"], queryFn: devicesApi.list });
  const bus = useQuery({ queryKey: ["business-units"], queryFn: buApi.list });

  const create = useMutation({
    mutationFn: () =>
      devicesApi.create({
        device_uid: form.device_uid,
        alias: form.alias,
        un_id: form.un_id || bus.data?.[0]?.id || "",
      }),
    onSuccess: () => {
      setForm({ device_uid: "", alias: "", un_id: "" });
      setError("");
      qc.invalidateQueries({ queryKey: ["devices"] });
    },
    onError: (e) => setError(errorMessage(e)),
  });

  if (devices.isLoading) return <Loading />;
  if (devices.error) return <ErrorBox message={errorMessage(devices.error)} />;

  const unName = (id: string) => bus.data?.find((u) => u.id === id)?.code ?? id;

  return (
    <>
      <PageHeader
        title="Dispositivos"
        subtitle="Registro y gestión de dispositivos móviles autorizados, vinculados a una UN (RF-WEB-02.3)."
      />

      {isOperator && (
        <div className="card" style={{ marginBottom: "1.5rem" }}>
          <h3 style={{ marginTop: 0 }}>Registrar dispositivo</h3>
          {error && <ErrorBox message={error} />}
          <div className="grid cols-3">
            <div>
              <label>Identificador (device UID)</label>
              <input
                value={form.device_uid}
                onChange={(e) => setForm({ ...form, device_uid: e.target.value })}
              />
            </div>
            <div>
              <label>Alias</label>
              <input value={form.alias} onChange={(e) => setForm({ ...form, alias: e.target.value })} />
            </div>
            <div>
              <label>Unidad de Negocio</label>
              <select value={form.un_id} onChange={(e) => setForm({ ...form, un_id: e.target.value })}>
                {(bus.data ?? []).map((u) => (
                  <option key={u.id} value={u.id}>
                    {u.code} — {u.name}
                  </option>
                ))}
              </select>
            </div>
          </div>
          <button className="btn" disabled={create.isPending} onClick={() => create.mutate()}>
            Registrar
          </button>
        </div>
      )}

      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Alias</th>
              <th>Device UID</th>
              <th>UN</th>
              <th>Params calidad</th>
              <th>Estado</th>
            </tr>
          </thead>
          <tbody>
            {devices.data!.map((d) => (
              <tr key={d.id}>
                <td>{d.alias}</td>
                <td className="muted">{d.device_uid}</td>
                <td>{unName(d.un_id)}</td>
                <td>{d.quality_params_version ?? "—"}</td>
                <td>
                  <span className={`badge ${d.active ? "green" : "gray"}`}>
                    {d.active ? "Activo" : "Inactivo"}
                  </span>
                </td>
              </tr>
            ))}
            {devices.data!.length === 0 && (
              <tr>
                <td colSpan={5} className="empty">
                  No hay dispositivos registrados.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </>
  );
}
