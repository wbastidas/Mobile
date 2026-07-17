import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { qualityApi } from "@/api/endpoints";
import { errorMessage } from "@/api/client";
import { useAuth } from "@/auth/AuthContext";
import { ErrorBox, Loading, PageHeader } from "@/components/ui";

const SAMPLE = JSON.stringify(
  {
    rules: {
      POSTE: [
        { field: "material", type: "domain", values: ["HORMIGON", "MADERA", "METAL"] },
        { field: "altura_m", type: "range", min: 6, max: 20 },
        { rule: "min_photos", value: 2 },
      ],
    },
  },
  null,
  2
);

export default function Quality() {
  const qc = useQueryClient();
  const { isAdmin } = useAuth();
  const [error, setError] = useState("");
  const [description, setDescription] = useState("");
  const [rules, setRules] = useState(SAMPLE);

  const params = useQuery({ queryKey: ["quality"], queryFn: qualityApi.list });

  const upload = useMutation({
    mutationFn: () => {
      let parsed: unknown;
      try {
        parsed = JSON.parse(rules);
      } catch {
        throw new Error("El JSON de reglas no es válido.");
      }
      return qualityApi.upload({ description, rules_json: parsed, activate: true });
    },
    onSuccess: () => {
      setError("");
      qc.invalidateQueries({ queryKey: ["quality"] });
    },
    onError: (e) => setError(e instanceof Error ? e.message : errorMessage(e)),
  });

  if (params.isLoading) return <Loading />;
  if (params.error) return <ErrorBox message={errorMessage(params.error)} />;

  return (
    <>
      <PageHeader
        title="Parámetros de calidad"
        subtitle="Carga y versionamiento de reglas de validación distribuidas a los dispositivos (RF-WEB-10)."
      />

      {isAdmin && (
        <div className="card" style={{ marginBottom: "1.5rem" }}>
          <h3 style={{ marginTop: 0 }}>Cargar nueva versión</h3>
          {error && <ErrorBox message={error} />}
          <label>Descripción</label>
          <input value={description} onChange={(e) => setDescription(e.target.value)} />
          <label>Reglas (JSON)</label>
          <textarea
            value={rules}
            onChange={(e) => setRules(e.target.value)}
            rows={12}
            style={{ fontFamily: "monospace", fontSize: "0.82rem" }}
          />
          <button className="btn" disabled={upload.isPending} onClick={() => upload.mutate()}>
            Publicar y activar
          </button>
        </div>
      )}

      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Versión</th>
              <th>Descripción</th>
              <th>Estado</th>
            </tr>
          </thead>
          <tbody>
            {params.data!.map((p) => (
              <tr key={p.id}>
                <td>v{p.version}</td>
                <td>{p.description ?? "—"}</td>
                <td>
                  <span className={`badge ${p.is_active ? "green" : "gray"}`}>
                    {p.is_active ? "Vigente" : "Histórica"}
                  </span>
                </td>
              </tr>
            ))}
            {params.data!.length === 0 && (
              <tr>
                <td colSpan={3} className="empty">
                  No hay versiones cargadas.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </>
  );
}
