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

/* ── marqueurs capteurs (VIIRS + MODIS) par pays d'Afrique centrale ── */
// Centres approximatifs des 8 pays du jeu de données FIRMS (slugs validés).
// Les capteurs VIIRS SNPP + MODIS Terra/Aqua couvrent l'ensemble de ces emprises.
const SENSOR_COUNTRIES = [
  { lat: 7.37,  lon: 12.35,  country: "Cameroun",             slug: "Cameroon" },
  { lat: 14.50, lon: 18.50,  country: "Tchad",                slug: "Chad" },
  { lat: 9.00,  lon: 20.00,  country: "RCA",                  slug: "Central_African_Republic" },
  { lat: 0.60,  lon: 11.40,  country: "Gabon",                slug: "Gabon" },
  { lat: 0.50,  lon: 15.20,  country: "Congo (Brazzaville)",  slug: "Republic_of_Congo" },
  { lat: -3.00, lon: 21.50,  country: "DRC",                  slug: "Democratic_Republic_of_the_Congo" },
  { lat: 1.80,  lon: 9.50,   country: "Guinée équatoriale",   slug: "Equatorial_Guinea" },
  { lat: 0.20,  lon: 6.60,   country: "São Tomé-et-Principe", slug: "Sao_Tome_and_Principe" },
];

/* 4 capteurs distincts — couleur + forme propres (pas de chevauchement).
   Chaque pays reçoit 4 marqueurs disposés en losange compact (±0,25°). */
const SENSORS = [
  { id: "viirs",  label: "VIIRS SNPP",  color: "#f08232", glyph: "●", desc: "Suomi-NPP 375 m · IR39" },
  { id: "terra",  label: "MODIS Terra", color: "#e05a4e", glyph: "■", desc: "Terra 1 km · IR36/IR38" },
  { id: "aqua",   label: "MODIS Aqua",  color: "#4ecdc4", glyph: "▲", desc: "Aqua 1 km · IR36/IR38" },
  { id: "viirs2", label: "VIIRS JPSS",  color: "#9b7bd6", glyph: "◆", desc: "JPSS 375 m · IR39" },
];

// 4 positions en losange autour du centre du pays
const DIAMOND = [
  { dx: 0,    dy:  0.45 }, // haut
  { dx:  0.45, dy: 0    }, // droite
  { dx: 0,    dy: -0.45 }, // bas
  { dx: -0.45, dy: 0    }, // gauche
];

function sensorMarker(coords, sensor, pos) {
  const lat = coords[0] + pos.dy;
  const lon = coords[1] + pos.dx;
  const layer = L.circleMarker([lat, lon], {
    radius: 8,
    color: "#fff",
    weight: 1.5,
    fillColor: sensor.color,
    fillOpacity: 0.9,
  });
  layer.bindPopup(
    `<b style="color:${sensor.color}">${sensor.glyph} ${sensor.label}</b><br>` +
    `<small>${sensor.desc}</small><br>` +
    `<small style="opacity:0.6">FIRMS open-access · 2019–2025</small>`
  );
  return layer;
}

function SensorMarkers({ show = false }) {
  const map = useMap();
  const ref = useRef(null);

  useEffect(() => {
    if (ref.current) { ref.current.eachLayer((l) => map.removeLayer(l)); ref.current = null; }
    if (!show) return;

    const markers = [];
    for (const c of SENSOR_COUNTRIES) {
      SENSORS.forEach((s, i) => {
        markers.push(sensorMarker([c.lat, c.lon], s, DIAMOND[i]));
      });
    }
    ref.current = L.layerGroup(markers).addTo(map);

    return () => {
      if (ref.current) { ref.current.eachLayer((l) => map.removeLayer(l)); ref.current = null; }
    };
  }, [show, map]);

  return null;
}

/** Légende des 4 capteurs — coin haut-droite, discrète. */
function SensorLegend({ show }) {
  if (!show) return null;
  return (
    <div className="sensor-legend" style={{
      position: "absolute",
      top: "calc(var(--hh, 4rem) + 0.8rem)",
      right: "0.8rem",
      zIndex: 1100,
      background: "rgba(14,46,41,0.82)",
      borderRadius: "0.5rem",
      padding: "0.55rem 0.75rem",
      color: "#fff",
      fontSize: "0.7rem",
      backdropFilter: "blur(4px)",
    }}>
      <div style={{ fontWeight: 700, fontSize: "0.74rem", marginBottom: "0.35rem", opacity: 0.9 }}>Capteurs</div>
      {SENSORS.map((s) => (
        <div key={s.id} style={{ display: "flex", alignItems: "center", gap: "0.4rem", marginBottom: "0.22rem" }}>
          <span style={{ color: s.color, fontSize: "0.85rem", width: "0.9rem", textAlign: "center" }}>{s.glyph}</span>
          <span style={{ opacity: 0.85 }}>{s.label}</span>
        </div>
      ))}
    </div>
  );
}

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
        const origin = riskData?.data_origin || "provenance ?";
        const gen = riskData?.generated_at
          ? new Date(riskData.generated_at).toLocaleDateString("fr-FR")
          : "?";
        layer.bindPopup(
          `<b>Cellule (${f.properties.cell_i}, ${f.properties.cell_j})</b><br>` +
          `Probabilité : ${(f.properties.prob * 100).toFixed(1)}%<br>` +
          `Niveau : ${riskLabel(f.properties.prob)}<br>` +
          `<small>${origin} · généré le ${gen}</small>`
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

export default function MapView({ activeBase, showRisk, riskThreshold, riskData, mapRef, onViewChange, showSensorMarkers = true }) {
  const resolvedRef = mapRef || useRef(null);
  const handleReady = useCallback(
    (m) => { resolvedRef.current = m; },
    [resolvedRef]
  );

  const riskGeoJSON = buildRiskGeoJSON(riskData?.cells, riskThreshold);

  return (
    <>
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

      {/* marqueurs capteurs */}
      <SensorMarkers show={showSensorMarkers} />

      <MapReady onReady={handleReady} />
      <ZoomControl position="bottomright" />
    </MapContainer>

    {/* légende capteurs (overlay au-dessus de la carte) */}
    <SensorLegend show={showSensorMarkers} />
    </>
  );
}
