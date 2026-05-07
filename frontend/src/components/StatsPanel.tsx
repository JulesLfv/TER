type SummaryItem = {
  method: string;
  tech: string;
  is_covered: boolean;
  length_km?: number;
  nb_points?: number;
  coverage_ratio?: number;
};

type CompareItem = {
  tech: string;
  operator_id?: number;
  operator_name?: string;
  a_covered_km?: number;
  b_covered_km?: number;
  a_ratio?: number;
  b_ratio?: number;
};

function formatKm(value: number) {
  return `${value.toLocaleString("fr-FR", { maximumFractionDigits: 1 })} km`;
}

function formatPercent(value: number) {
  return `${(value * 100).toLocaleString("fr-FR", { maximumFractionDigits: 1 })} %`;
}

export function StatsPanel({ stats, compare }: { stats?: { items?: SummaryItem[] }; compare?: { items?: CompareItem[] } }) {
  const allItems = stats?.items ?? [];
  const hasOfficial = allItems.some((item) => item.method === "B_OFFICIAL");
  const hasTheoretical = allItems.some((item) => item.method === "A_THEORETICAL");
  const method = hasOfficial ? "B_OFFICIAL" : hasTheoretical ? "A_THEORETICAL" : undefined;
  const items = method ? allItems.filter((item) => item.method === method) : allItems;
  const coveredKm = items.filter((item) => item.is_covered).reduce((sum, item) => sum + (item.length_km ?? 0), 0);
  const uncoveredKm = items.filter((item) => !item.is_covered).reduce((sum, item) => sum + (item.length_km ?? 0), 0);
  const totalKm = coveredKm + uncoveredKm;
  const ratio = totalKm > 0 ? coveredKm / totalKm : 0;
  const points = items.reduce((sum, item) => sum + (item.nb_points ?? 0), 0);

  return (
    <div style={{ marginTop: "1rem" }}>
      <strong>Statistiques</strong>
      {method && <p style={{ margin: "0.35rem 0" }}>KPI calculés sur {method}.</p>}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.5rem", marginTop: "0.5rem" }}>
        <div>
          <small>Couverts</small>
          <div>{formatKm(coveredKm)}</div>
        </div>
        <div>
          <small>Non couverts</small>
          <div>{formatKm(uncoveredKm)}</div>
        </div>
        <div>
          <small>Couverture</small>
          <div>{formatPercent(ratio)}</div>
        </div>
        <div>
          <small>Points</small>
          <div>{points.toLocaleString("fr-FR")}</div>
        </div>
      </div>

      <strong style={{ display: "block", marginTop: "1rem" }}>Comparaison A/B</strong>
      {(compare?.items ?? []).length > 0 ? (
        <div style={{ overflowX: "auto", marginTop: "0.5rem" }}>
          <table style={{ borderCollapse: "collapse", width: "100%", fontSize: "0.9rem" }}>
            <thead>
              <tr>
                <th style={{ textAlign: "left" }}>Opérateur</th>
                <th style={{ textAlign: "right" }}>A</th>
                <th style={{ textAlign: "right" }}>B</th>
              </tr>
            </thead>
            <tbody>
          {(compare?.items ?? []).map((item) => (
            <tr key={`${item.tech}-${item.operator_id ?? item.operator_name}`}>
              <td>{item.operator_name ?? `Opérateur ${item.operator_id ?? ""}`}</td>
              <td style={{ textAlign: "right" }}>{formatPercent(item.a_ratio ?? 0)}</td>
              <td style={{ textAlign: "right" }}>{formatPercent(item.b_ratio ?? 0)}</td>
            </tr>
          ))}
            </tbody>
          </table>
        </div>
      ) : (
        <p>Aucune statistique disponible.</p>
      )}
    </div>
  );
}
