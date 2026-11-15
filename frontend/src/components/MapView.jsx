/**
 * MapView — carte Leaflet via react-leaflet.
 *
 * Props:
 *  - activeBase: "esri" | "viirs" | "blueMarble" | "smoke"
 *  - showRisk: boolean
 *  - riskThreshold: number 0–100
 *  - riskData: object | null (fire_risk.json)
 *  - mapRef: MutableRefObject vers la carte Leaflet native (optionnel)
 *  - onViewChange: callback quand l'utilisateur zoome/vol
 */

import { useEffect, useRef, useCallback } from "react";
import { MapContainer, TileLayer, useMap, ZoomControl } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import { VIEWS, GIBS_DATE, CAM_BBOX, RISK_GRID, RISK_LEVELS } from "../data/constants.js";

/* ── helpers risque ── */
function riskLabel(prob) {
  for (let i = RISK_LEVELS.length - 1; i >= 0; i--) {
    if (prob >= RISK_LEVELS[i].min) return RISK_LEVELS[i].label;
  }
  return RISK_LEVELS[0].label;
}
function riskColor(prob) {
  for (let i = RISK_LEVELS.length - 1; i >= 0; i--) {
    if (prob >= RISK_LEVELS[i].min) return RISK_LEVELS[i].color;
  }
  return RISK_LEVELS[0].color;
}

/* ── tuiles GIBS ── */
const TILES = {
  esri: {
    url: "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
    opts: { maxZoom: 18, attribution: "Earthstar Geographics | Esri" },
  },
  viirs: {
    url: `https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/VIIRS_SNPP_CorrectedReflectance_TrueColor/default/${GIBS_DATE}/GoogleMapsCompatible_Level9/{z}/{y}/{x}.jpg`,
    opts: { maxNativeZoom: 9, maxZoom: 18, attribution: "NASA GIBS – VIIRS SNPP" },
  },
  blueMarble: {
    url: `https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/BlueMarble_ShadedRelief_Bathymetry/default/GoogleMapsCompatible_Level8/{z}/{y}/{x}.jpeg`,
    opts: { maxNativeZoom: 8, maxZoom: 18, attribution: "NASA GIBS – Blue Marble" },
  },
  labels: {
    url: "https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}",
    opts: { maxZoom: 18, opacity: 0.9 },
  },
  hotspots: {
    url: `https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/VIIRS_SNPP_Thermal_Anomalies_375m_All/default/${GIBS_DATE}/GoogleMapsCompatible_Level8/{z}/{y}/{x}.png`,
    opts: { maxNativeZoom: 8, maxZoom: 18, attribution: "NASA FIRMS / GIBS" },
  },
  aerosols: {
    url: `https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/MODIS_Terra_Aerosol/default/${GIBS_DATE}/GoogleMapsCompatible_Level6/{z}/{y}/{x}.png`,
    opts: { maxNativeZoom: 6, maxZoom: 18, opacity: 0.65 },
  },
};

/* ── composant interne qui expose la map Leaflet native ── */
function MapReady({ onReady }) {
  const map = useMap();
  useEffect(() => {
    onReady?.(map);
    return () => onReady?.(null);
  }, [map, onReady]);
  return null;
}

/* ── couche GeoJSON risque ── */
function RiskGeoJSONLayer({ geoJSON, riskData }) {
  const map = useMap();
  const ref = useRef(null);

  useEffect(() => {
    if (ref.current) { map.removeLayer(ref.current); ref.current = null; }
    if (!geoJSON?.features?.length) return;

    ref.current = L.geoJSON(geoJSON, {
      style(f) {
        const p = f.properties.prob;
        return {
          color: "transparent", weight: 0,
          fillColor: riskColor(p), fillOpacity: 0.55,
          className: "risk-cell", interactive: true,
        };
      },
      onEachFeature(f, layer) {
        const origin = riskData?.data_origin || "unknown provenance";
        const gen = riskData?.generated_at
          ? new Date(riskData.generated_at).toLocaleDateString("en-GB")
          : "?";
        layer.bindPopup(
          `<b>Cell (${f.properties.cell_i}, ${f.properties.cell_j})</b><br>` +
          `Probability: ${(f.properties.prob * 100).toFixed(1)}%<br>` +
          `Level: ${riskLabel(f.properties.prob)}<br>` +
          `<small>${origin} · generated ${gen}</small>`
        );
      },
    }).addTo(map);

    return () => {
      if (ref.current) { map.removeLayer(ref.current); ref.current = null; }
    };
  }, [geoJSON, riskData, map]);

  return null;
}

/**
 * Construit le FeatureCollection GeoJSON des cellules de risque.
 */
export function buildRiskGeoJSON(cells, threshold) {
  if (!cells) return { type: "FeatureCollection", features: [] };
  const features = [];
  for (const c of cells) {
    if (c.prob < threshold) continue;
    const lat = c.lat ?? CAM_BBOX[1] + c.cell_j * RISK_GRID + RISK_GRID / 2;
    const lon = c.lon ?? CAM_BBOX[0] + c.cell_i * RISK_GRID + RISK_GRID / 2;
    if (lat < CAM_BBOX[1] || lat > CAM_BBOX[3] || lon < CAM_BBOX[0] || lon > CAM_BBOX[2]) continue;
    features.push({
      type: "Feature",
      properties: { cell_i: c.cell_i, cell_j: c.cell_j, prob: c.prob },
      geometry: {
        type: "Polygon",
        coordinates: [[
          [lon - RISK_GRID / 2, lat - RISK_GRID / 2],
          [lon + RISK_GRID / 2, lat - RISK_GRID / 2],
          [lon + RISK_GRID / 2, lat + RISK_GRID / 2],
          [lon - RISK_GRID / 2, lat + RISK_GRID / 2],
          [lon - RISK_GRID / 2, lat - RISK_GRID / 2],
        ]],
      },
    });
  }
  return { type: "FeatureCollection", features };
}

export default function MapView({ activeBase, showRisk, riskThreshold, riskData, mapRef, onViewChange }) {
  const resolvedRef = mapRef || useRef(null);
  const handleReady = useCallback(
    (m) => { resolvedRef.current = m; },
    [resolvedRef]
  );

  const riskGeoJSON = buildRiskGeoJSON(riskData?.cells, riskThreshold);

  return (
    <MapContainer
      center={VIEWS.africa.center}
      zoom={VIEWS.africa.zoom}
      minZoom={2}
      maxZoom={18}
      zoomControl={false}
      worldCopyJump
      style={{ height: "100%", width: "100%" }}
    >
      {/* fond principal Esri */}
      <TileLayer url={TILES.esri.url} {...TILES.esri.opts} zIndex={0} />

      {/* fond alternatif */}
      {activeBase === "viirs" && <TileLayer url={TILES.viirs.url} {...TILES.viirs.opts} zIndex={1} />}
      {activeBase === "blueMarble" && <TileLayer url={TILES.blueMarble.url} {...TILES.blueMarble.opts} zIndex={1} />}

      {/* labels */}
      <TileLayer url={TILES.labels.url} {...TILES.labels.opts} zIndex={2} />

      {/* hotspots */}
      <TileLayer url={TILES.hotspots.url} {...TILES.hotspots.opts} zIndex={3} />

      {/* aérosols */}
      {activeBase === "smoke" && <TileLayer url={TILES.aerosols.url} {...TILES.aerosols.opts} zIndex={3} />}

      {/* risque */}
      <RiskGeoJSONLayer geoJSON={showRisk ? riskGeoJSON : null} riskData={riskData} />

      <MapReady onReady={handleReady} />
      <ZoomControl position="bottomright" />
    </MapContainer>
  );
}
