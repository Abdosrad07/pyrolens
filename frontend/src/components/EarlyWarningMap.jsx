/**
 * EarlyWarningMap — carte Leaflet dédiée du Early Warning Center.
 *
 * Réutilise la même infrastructure TILES que MapView (pas de nouveau moteur).
 * Affiche les cellules d'alerte en fonction de leur sévérité, synchronisée
 * avec la liste (props : alerts, selected, onSelect).
 */

import { useEffect, useRef } from "react";
import { MapContainer, TileLayer, useMap, ZoomControl } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import { VIEWS } from "../data/constants.js";

/* ── couleurs de sévérité (cohérentes avec la palette ember/sulphur/lagoon) ── */
const SEV = {
  critical: { color: "#A4201B", bg: "rgba(164,32,27,0.55)", r: 12 },
  high:     { color: "#F2541B", bg: "rgba(242,84,27,0.5)", r: 10 },
  moderate: { color: "#FFC83D", bg: "rgba(255,200,61,0.45)", r: 8 },
  low:      { color: "#168F80", bg: "rgba(22,143,128,0.4)", r: 6 },
};

/**
 * Couche des cellules d'alerte.
 * Reconstruit les marqueurs quand alerts/selected changent.
 */
function AlertCells({ alerts, selected, onSelect }) {
  const map = useMap();
  const ref = useRef(null);

  useEffect(() => {
    if (ref.current) { ref.current.eachLayer((l) => map.removeLayer(l)); ref.current = null; }
    if (!alerts?.length) return;

    ref.current = L.layerGroup(
      alerts.map((a) => {
        // Gérer les coordonnées manquantes
        if (a.lat == null || a.lon == null || Number.isNaN(a.lat) || Number.isNaN(a.lon)) {
          return L.marker([0, 0], {
            opacity: 0,
            interactive: false,
            icon: L.divIcon({ className: "ew-hidden", html: "" }),
          }).bindPopup("<small>Coordonnées indisponibles</small>");
        }

        const s = SEV[a.severity] || SEV.low;
        const isSel = selected?.cell_id === a.cell_id;
        const marker = L.circleMarker([a.lat, a.lon], {
          radius: isSel ? s.r + 4 : s.r,
          color: "#fff",
          weight: isSel ? 3 : 1.5,
          fillColor: s.color,
          fillOpacity: isSel ? 0.85 : 0.55,
        }).bindPopup(
          `<b style="color:${s.color}">${a.severity.toUpperCase()}</b> · cellule ${a.cell_id}<br>` +
          `${a.lat.toFixed(2)}°, ${a.lon.toFixed(2)}°<br>` +
          `<small>Récent : ${a.recent_detections} · Baseline : ${a.historical_baseline}</small>`
        );
        marker.on("click", () => onSelect?.(a));
        return marker;
      })
    ).addTo(map);

    return () => {
      if (ref.current) { ref.current.eachLayer((l) => map.removeLayer(l)); ref.current = null; }
    };
  }, [alerts, selected, onSelect, map]);

  return null;
}

/**
 * Fit des bornes sur les cellules d'alerte (une fois la carte prête).
 */
function FitBounds({ alerts }) {
  const map = useMap();
  const fitted = useRef(false);

  useEffect(() => {
    if (fitted.current || !alerts?.length) return;
    const pts = alerts.filter((a) => a.lat != null && a.lon != null).map((a) => [a.lat, a.lon]);
    if (!pts.length) return;
    map.fitBounds(L.latLngBounds(pts).pad(0.3), { animate: true });
    fitted.current = true;
  }, [alerts, map]);

  return null;
}

/** Légende des niveaux d'alerte. */
function MapLegend() {
  return (
    <div style={{
      position: "absolute", top: "0.8rem", left: "0.8rem", zIndex: 1100,
      background: "rgba(14,42,41,0.85)", borderRadius: "0.5rem",
      padding: "0.6rem 0.8rem", color: "#fff", fontSize: "0.72rem",
      backdropFilter: "blur(4px)", boxShadow: "0 2px 8px rgba(0,0,0,0.25)",
    }}>
      <div style={{ fontWeight: 700, fontSize: "0.78rem", marginBottom: "0.4rem" }}>Niveau d'alerte</div>
      {Object.entries(SEV).map(([k, v]) => (
        <div key={k} style={{ display: "flex", alignItems: "center", gap: "0.4rem", marginBottom: "0.25rem" }}>
          <span style={{ width: 12, height: 12, borderRadius: "50%", background: v.color, flex: "none", border: "1.5px solid #fff" }} />
          <span style={{ textTransform: "capitalize", opacity: 0.9 }}>{k}</span>
        </div>
      ))}
    </div>
  );
}

export default function EarlyWarningMap({ alerts, selected, onSelect }) {
  return (
    <div style={{ position: "relative", width: "100%", height: "100%", borderRadius: "var(--r-m)", overflow: "hidden" }}>
      <MapContainer
        center={VIEWS.africa.center}
        zoom={VIEWS.africa.zoom}
        minZoom={3}
        maxZoom={12}
        zoomControl={false}
        style={{ height: "100%", width: "100%" }}
      >
        <TileLayer
          url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
          attribution="Esri · PyroLens"
          maxZoom={18}
        />
        <TileLayer
          url="https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}"
          opacity={0.9}
          zIndex={2}
        />
        <AlertCells alerts={alerts} selected={selected} onSelect={onSelect} />
        <FitBounds alerts={alerts} />
        <ZoomControl position="bottomright" />
      </MapContainer>
      <MapLegend />
    </div>
  );
}
