type Props = {
  showRoutes: boolean;
  showSites: boolean;
  showCoveragePoints: boolean;
  onShowRoutesChange: (value: boolean) => void;
  onShowSitesChange: (value: boolean) => void;
  onShowCoveragePointsChange: (value: boolean) => void;
};

export function LayerControl({
  showRoutes,
  showSites,
  showCoveragePoints,
  onShowRoutesChange,
  onShowSitesChange,
  onShowCoveragePointsChange,
}: Props) {
  return (
    <div style={{ marginTop: "1rem" }}>
      <strong>Couches</strong>
      <div style={{ display: "grid", gap: "0.35rem", marginTop: "0.5rem" }}>
        <label>
          <input type="checkbox" checked={showRoutes} onChange={(e) => onShowRoutesChange(e.target.checked)} /> Routes
        </label>
        <label>
          <input type="checkbox" checked={showSites} onChange={(e) => onShowSitesChange(e.target.checked)} /> Antennes
        </label>
        <label>
          <input
            type="checkbox"
            checked={showCoveragePoints}
            onChange={(e) => onShowCoveragePointsChange(e.target.checked)}
          />{" "}
          Points couverts/non couverts
        </label>
      </div>
      <strong>Légende méthode</strong>
      <ul style={{ paddingLeft: "1.2rem", marginTop: "0.5rem" }}>
        <li>A_THEORETICAL: approximation par distance aux sites radio.</li>
        <li>B_OFFICIAL: couverture issue d'une couche officielle.</li>
      </ul>
    </div>
  );
}
