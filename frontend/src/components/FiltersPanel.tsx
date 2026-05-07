type Props = {
  tech: string;
  antennaTech: string;
  operatorId: string;
  operators: { id: number; name: string }[];
  pilotLabel: string;
  pilotBbox: string;
  regionCode: string;
  deptCode: string;
  onTechChange: (v: string) => void;
  onAntennaTechChange: (v: string) => void;
  onOperatorChange: (v: string) => void;
  onRegionChange: (v: string) => void;
  onDeptChange: (v: string) => void;
  onApply: () => void;
};

export function FiltersPanel({
  tech,
  antennaTech,
  operatorId,
  operators,
  pilotLabel,
  pilotBbox,
  regionCode,
  deptCode,
  onTechChange,
  onAntennaTechChange,
  onOperatorChange,
  onRegionChange,
  onDeptChange,
  onApply,
}: Props) {
  return (
    <div style={{ display: "grid", gap: "0.75rem" }}>
      <strong>Filtres</strong>
      <div>
        <small>Zone active</small>
        <div>{pilotLabel}</div>
        <small>{pilotBbox}</small>
      </div>
      <div>
        <label>Stats/couverture: </label>
        <select value={tech} onChange={(e) => onTechChange(e.target.value)}>
          <option value="">Toutes</option>
          <option value="4G">4G</option>
          <option value="5G">5G</option>
        </select>
      </div>
      <div>
        <label>Antennes: </label>
        <select value={antennaTech} onChange={(e) => onAntennaTechChange(e.target.value)}>
          <option value="">4G + 5G</option>
          <option value="4G">4G seulement</option>
          <option value="5G">5G seulement</option>
        </select>
      </div>
      <div>
        <label>Opérateur: </label>
        <select value={operatorId} onChange={(e) => onOperatorChange(e.target.value)}>
          <option value="">Tous</option>
          {operators.map((operator) => (
            <option key={operator.id} value={operator.id}>
              {operator.name}
            </option>
          ))}
        </select>
      </div>
      <div>
        <label>Région: </label>
        <input value={regionCode} onChange={(e) => onRegionChange(e.target.value)} placeholder="ex: 11" />
      </div>
      <div>
        <label>Département: </label>
        <input value={deptCode} onChange={(e) => onDeptChange(e.target.value)} placeholder="ex: 75" />
      </div>
      <button onClick={onApply} type="button">Appliquer</button>
    </div>
  );
}
