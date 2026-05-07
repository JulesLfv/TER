import { useEffect } from "react";
import L from "leaflet";
import { CircleMarker, GeoJSON, MapContainer, Popup, TileLayer } from "react-leaflet";

type Props = {
  segments?: any;
  sites?: any;
  coveragePoints?: any;
  showRoutes: boolean;
  showSites: boolean;
  showCoveragePoints: boolean;
};

export function MapView({ segments, sites, coveragePoints, showRoutes, showSites, showCoveragePoints }: Props) {
  useEffect(() => {}, [segments, sites, coveragePoints]);
  const points = coveragePoints?.features ?? [];
  const sitePoints = sites?.features ?? [];

  return (
    <MapContainer center={[44.65, 3.5]} zoom={10} style={{ height: "80vh", width: "100%" }}>
      <TileLayer
        attribution='&copy; OpenStreetMap contributors'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      {showRoutes && segments && <GeoJSON data={segments} style={{ color: "#1f77b4", weight: 2 }} />}
      {showSites &&
        sitePoints.map((feature: any) => {
          const [lng, lat] = feature.geometry.coordinates;
          const props = feature.properties ?? {};
          return (
            <CircleMarker
              key={`site-${feature.id}`}
              center={new L.LatLng(lat, lng)}
              radius={5}
              pathOptions={{
                color: props.tech === "5G" ? "#7c3aed" : "#d62728",
                fillColor: props.tech === "5G" ? "#a78bfa" : "#f87171",
                fillOpacity: 0.85,
                weight: 1,
              }}
            >
              <Popup>
                <strong>{props.operator_name ?? `Opérateur ${props.operator_id ?? ""}`}</strong>
                <br />
                Techno: {props.tech ?? "?"}
                <br />
                Site: {props.site_id ?? "n/a"}
                <br />
                Bande: {props.band ?? "n/a"}
              </Popup>
            </CircleMarker>
          );
        })}
      {showCoveragePoints && points.map((feature: any) => {
        const [lng, lat] = feature.geometry.coordinates;
        const covered = feature.properties?.is_covered;
        return (
          <CircleMarker
            key={feature.id}
            center={new L.LatLng(lat, lng)}
            radius={3}
            pathOptions={{
              color: covered ? "#167a3a" : "#b42318",
              fillColor: covered ? "#2fbf71" : "#ef4444",
              fillOpacity: 0.8,
              weight: 1,
            }}
          />
        );
      })}
    </MapContainer>
  );
}
