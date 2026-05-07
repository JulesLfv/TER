import { useEffect, useState } from "react";
import { getJson } from "./lib/api";
import { MapView } from "./components/MapView";
import { FiltersPanel } from "./components/FiltersPanel";
import { LayerControl } from "./components/LayerControl";
import { StatsPanel } from "./components/StatsPanel";

const PILOT_BBOX = "3.20,44.40,3.80,44.90";
const PILOT_LABEL = "Lozère pilote";

export default function App() {
  const [operators, setOperators] = useState<any[]>([]);
  const [segments, setSegments] = useState<any>();
  const [sites, setSites] = useState<any>();
  const [coveragePoints, setCoveragePoints] = useState<any>();
  const [stats, setStats] = useState<any>();
  const [compare, setCompare] = useState<any>();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");

  const [tech, setTech] = useState("4G");
  const [antennaTech, setAntennaTech] = useState("");
  const [operatorId, setOperatorId] = useState("3");
  const [regionCode, setRegionCode] = useState("");
  const [deptCode, setDeptCode] = useState("");
  const [showRoutes, setShowRoutes] = useState(true);
  const [showSites, setShowSites] = useState(true);
  const [showCoveragePoints, setShowCoveragePoints] = useState(true);

  const loadData = async () => {
    try {
      setIsLoading(true);
      setError("");
      const op = operatorId ? Number(operatorId) : undefined;
      const commonFilters = {
        tech: tech || undefined,
        operator_id: op,
        region_code: regionCode || undefined,
        dept_code: deptCode || undefined,
      };
      const geoFilters = {
        bbox: PILOT_BBOX,
        region_code: regionCode || undefined,
        dept_code: deptCode || undefined,
      };
      const [seg, st, pts, s, cmp] = await Promise.all([
        getJson("/api/v1/roads/segments", { limit: 1000, ...geoFilters }),
        getJson("/api/v1/radio-sites", { limit: 2000, bbox: PILOT_BBOX, tech: antennaTech || undefined, operator_id: op }),
        getJson("/api/v1/coverage/sample-points", {
          limit: 30000,
          bbox: PILOT_BBOX,
          tech: tech || undefined,
          operator_id: op,
          method: "B_OFFICIAL",
        }),
        getJson("/api/v1/stats/summary", commonFilters),
        getJson("/api/v1/stats/compare", {
          tech: tech || undefined,
          region_code: regionCode || undefined,
          dept_code: deptCode || undefined,
        }),
      ]);
      setSegments(seg);
      setSites(st);
      setCoveragePoints(pts);
      setStats(s);
      setCompare(cmp);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erreur inconnue pendant le chargement");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    getJson("/api/v1/operators")
      .then((data) => setOperators(data.items ?? []))
      .catch(() => setOperators([]));
    loadData();
  }, []);

  return (
    <main style={{ display: "grid", gridTemplateColumns: "340px 1fr", gap: "1rem" }}>
      <aside>
        <h1>TER 4G/5G Routes</h1>
        <FiltersPanel
          tech={tech}
          antennaTech={antennaTech}
          operatorId={operatorId}
          operators={operators}
          pilotLabel={PILOT_LABEL}
          pilotBbox={PILOT_BBOX}
          regionCode={regionCode}
          deptCode={deptCode}
          onTechChange={setTech}
          onAntennaTechChange={setAntennaTech}
          onOperatorChange={setOperatorId}
          onRegionChange={setRegionCode}
          onDeptChange={setDeptCode}
          onApply={loadData}
        />
        {isLoading && <p>Chargement...</p>}
        {error && <p style={{ color: "#b00020" }}>{error}</p>}
        <LayerControl
          showRoutes={showRoutes}
          showSites={showSites}
          showCoveragePoints={showCoveragePoints}
          onShowRoutesChange={setShowRoutes}
          onShowSitesChange={setShowSites}
          onShowCoveragePointsChange={setShowCoveragePoints}
        />
        <StatsPanel stats={stats} compare={compare} />
      </aside>
      <section>
        <MapView
          segments={segments}
          sites={sites}
          coveragePoints={coveragePoints}
          showRoutes={showRoutes}
          showSites={showSites}
          showCoveragePoints={showCoveragePoints}
        />
      </section>
    </main>
  );
}
