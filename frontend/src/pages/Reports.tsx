import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { reportsApi } from "@/api/endpoints";
import { errorMessage } from "@/api/client";
import { ErrorBox, Loading, PageHeader } from "@/components/ui";

export default function Reports() {
  const [selected, setSelected] = useState("works-summary");
  const [downloading, setDownloading] = useState<string | null>(null);

  const catalog = useQuery({ queryKey: ["reports-catalog"], queryFn: reportsApi.catalog });
  const report = useQuery({
    queryKey: ["report", selected],
    queryFn: () => reportsApi.data(selected),
    enabled: !!selected,
  });

  const download = async (fmt: string) => {
    setDownloading(fmt);
    try {
      const blob = await reportsApi.download(selected, fmt);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${selected}.${fmt}`;
      a.click();
      URL.revokeObjectURL(url);
    } finally {
      setDownloading(null);
    }
  };

  const columns = report.data?.rows?.[0] ? Object.keys(report.data.rows[0]) : [];

  return (
    <>
      <PageHeader
        title="Reportes"
        subtitle="Generación y exportación de reportes (Excel / PDF / CSV), respetando la segregación de UN (RF-WEB-11)."
      />

      <div className="toolbar row between">
        <div style={{ width: 320 }}>
          <select value={selected} onChange={(e) => setSelected(e.target.value)} style={{ margin: 0 }}>
            {(catalog.data ?? []).map((r) => (
              <option key={r.key} value={r.key}>
                {r.name}
              </option>
            ))}
          </select>
        </div>
        <div className="row">
          <button className="btn secondary sm" disabled={!!downloading} onClick={() => download("xlsx")}>
            {downloading === "xlsx" ? "…" : "Excel"}
          </button>
          <button className="btn secondary sm" disabled={!!downloading} onClick={() => download("pdf")}>
            {downloading === "pdf" ? "…" : "PDF"}
          </button>
          <button className="btn secondary sm" disabled={!!downloading} onClick={() => download("csv")}>
            {downloading === "csv" ? "…" : "CSV"}
          </button>
        </div>
      </div>

      {report.isLoading ? (
        <Loading />
      ) : report.error ? (
        <ErrorBox message={errorMessage(report.error)} />
      ) : (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                {columns.map((c) => (
                  <th key={c}>{c.replace(/_/g, " ")}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {(report.data?.rows ?? []).map((row, i) => (
                <tr key={i}>
                  {columns.map((c) => (
                    <td key={c}>{String(row[c])}</td>
                  ))}
                </tr>
              ))}
              {(report.data?.rows ?? []).length === 0 && (
                <tr>
                  <td colSpan={Math.max(1, columns.length)} className="empty">
                    Sin datos para este reporte.
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
