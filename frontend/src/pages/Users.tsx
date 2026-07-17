import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { buApi, usersApi } from "@/api/endpoints";
import { errorMessage } from "@/api/client";
import { ErrorBox, Loading, PageHeader } from "@/components/ui";
import type { Role } from "@/types";

const ROLES: { value: Role; label: string }[] = [
  { value: "ADMIN", label: "Administrador" },
  { value: "OPERATOR_MATRIZ", label: "Operador Matriz" },
  { value: "OPERATOR_UN", label: "Operador UN" },
  { value: "VIEWER_MATRIZ", label: "Visualizador Matriz" },
  { value: "VIEWER_UN", label: "Visualizador UN" },
  { value: "FIELD", label: "Funcionario de campo" },
];

const GLOBAL_ROLES: Role[] = ["ADMIN", "OPERATOR_MATRIZ", "VIEWER_MATRIZ"];

export default function Users() {
  const qc = useQueryClient();
  const [error, setError] = useState("");
  const [form, setForm] = useState({
    username: "",
    full_name: "",
    role: "OPERATOR_UN" as Role,
    un_id: "",
    password: "",
  });

  const users = useQuery({ queryKey: ["users"], queryFn: usersApi.list });
  const bus = useQuery({ queryKey: ["business-units"], queryFn: buApi.list });

  const needsUn = !GLOBAL_ROLES.includes(form.role);

  const create = useMutation({
    mutationFn: () =>
      usersApi.create({
        username: form.username,
        full_name: form.full_name,
        role: form.role,
        auth_type: "LOCAL",
        un_id: needsUn ? form.un_id || bus.data?.[0]?.id : null,
        password: form.password,
      }),
    onSuccess: () => {
      setForm({ ...form, username: "", full_name: "", password: "" });
      setError("");
      qc.invalidateQueries({ queryKey: ["users"] });
    },
    onError: (e) => setError(errorMessage(e)),
  });

  if (users.isLoading) return <Loading />;
  if (users.error) return <ErrorBox message={errorMessage(users.error)} />;

  const unCode = (id: string | null) => (id ? bus.data?.find((u) => u.id === id)?.code ?? id : "Global");

  return (
    <>
      <PageHeader
        title="Usuarios"
        subtitle="Gestión de usuarios con asignación de rol y unidad de negocio (RF-WEB-02.1)."
      />

      <div className="card" style={{ marginBottom: "1.5rem" }}>
        <h3 style={{ marginTop: 0 }}>Crear usuario (local)</h3>
        {error && <ErrorBox message={error} />}
        <div className="grid cols-3">
          <div>
            <label>Usuario</label>
            <input value={form.username} onChange={(e) => setForm({ ...form, username: e.target.value })} />
          </div>
          <div>
            <label>Nombre completo</label>
            <input value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} />
          </div>
          <div>
            <label>Rol</label>
            <select value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value as Role })}>
              {ROLES.map((r) => (
                <option key={r.value} value={r.value}>
                  {r.label}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label>Unidad de Negocio {needsUn ? "(requerida)" : "(no aplica)"}</label>
            <select
              value={form.un_id}
              disabled={!needsUn}
              onChange={(e) => setForm({ ...form, un_id: e.target.value })}
            >
              {(bus.data ?? []).map((u) => (
                <option key={u.id} value={u.id}>
                  {u.code} — {u.name}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label>Contraseña</label>
            <input
              type="password"
              value={form.password}
              onChange={(e) => setForm({ ...form, password: e.target.value })}
            />
          </div>
        </div>
        <button className="btn" disabled={create.isPending} onClick={() => create.mutate()}>
          Crear usuario
        </button>
      </div>

      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Usuario</th>
              <th>Nombre</th>
              <th>Rol</th>
              <th>Ámbito</th>
              <th>Estado</th>
            </tr>
          </thead>
          <tbody>
            {users.data!.map((u) => (
              <tr key={u.id}>
                <td>{u.username}</td>
                <td>{u.full_name}</td>
                <td>{ROLES.find((r) => r.value === u.role)?.label ?? u.role}</td>
                <td>{unCode(u.un_id)}</td>
                <td>
                  <span className={`badge ${u.active ? "green" : "gray"}`}>
                    {u.active ? "Activo" : "Inactivo"}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}
