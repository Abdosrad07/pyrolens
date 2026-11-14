/**
 * App — composant racine de Fire Monitor.
 *
 * Gère l'état global :
 *  - view : "map" | "overview" | "calendar" | "jobs" | "dq" | "risk"
 *  - panneau cluster (WY)
 *  - panneau IA
 *  - panneau risque
 *  - toast
 */

import { useState, useEffect, useCallback } from "react";
import MapView from "./components/MapView.jsx";
import TopBar from "./components/TopBar.jsx";
import DockNav from "./components/DockNav.jsx";
import RiskSphere from "./components/RiskSphere.jsx";
import RiskPanel from "./components/RiskPanel.jsx";
import AiPanel from "./components/AiPanel.jsx";
import Toast from "./components/Toast.jsx";
import OverviewView from "./views/OverviewView.jsx";
import CalendarView from "./views/CalendarView.jsx";
import JobsView from "./views/JobsView.jsx";
import DqView from "./views/DqView.jsx";
import RiskView from "./views/RiskView.jsx";
import useMap from "./hooks/useMap.js";
import useRiskData from "./hooks/useRiskData.js";
import useApi from "./hooks/useApi.js";

const VIEWS = {
  map: "Carte",
  overview: "Aperçu",
  calendar: "Calendrier",
  jobs: "Jobs",
  dq: "Qualité des données",
  risk: "Risque de feu",
};

export default function App() {
  const [view, setView] = useState("map");
  const [aiOpen, setAiOpen] = useState(false);
  const [riskOpen, setRiskOpen] = useState(false);
  const [toastMsg, setToastMsg] = useState(null);
  const [showRisk, setShowRisk] = useState(true);
  const [riskThreshold, setRiskThreshold] = useState(0);

  const { mapRef, flyToView, flyToCoords, invalidateSize } = useMap();
  const { riskData, loading: riskLoading, reload: reloadRisk, origin, generatedAt, metrics, cellsCount, highCells } =
    useRiskData();
  const api = useApi();

  // Charger les données risque au montage
  useEffect(() => {
    if (!riskData) reloadRisk();
  }, []);

  const showRiskOnMap = showRisk && (view === "map" || view === "risk");

  const showToast = useCallback((msg) => setToastMsg(msg), []);
  const hideToast = useCallback(() => setToastMsg(null), []);

  const handleSearch = useCallback(async (q) => {
    showToast("Recherche…");
    const res = await api.geocode(q);
    if (res) {
      setView("map");
      flyToCoords(res.lat, res.lon, 8);
      showToast("Lieu localisé");
    } else {
      showToast("Lieu introuvable : essayez un nom de ville ou de pays");
    }
  }, [api, flyToCoords, showToast]);

  const handleAiSend = useCallback(async (q) => {
    const reply = await api.chat(
      [{ role: "user", content: q }],
      {
        view: { lat: 2, lon: 20, zoom: 4 },
        risk: riskData
          ? { origin, generated_at: riskData.generated_at, cells: riskData.cells?.length, threshold: riskThreshold, visible: showRisk }
          : null,
      }
    );
    return reply;
  }, [api, riskData, origin, riskThreshold, showRisk]);

  const handleNavSelect = useCallback((v) => {
    if (v === "risk") {
      setRiskOpen(true);
      if (!riskData) reloadRisk();
      return;
    }
    setView(v);
    setRiskOpen(false);
    setAiOpen(false);
    invalidateSize();
  }, [riskData, reloadRisk, invalidateSize]);

  const closeAllPanels = useCallback(() => {
    setAiOpen(false);
    setRiskOpen(false);
    invalidateSize();
  }, [invalidateSize]);

  // Échap global
  useEffect(() => {
    function onKey(e) {
      if (e.key === "Escape") {
        if (aiOpen) setAiOpen(false);
        else if (riskOpen) setRiskOpen(false);
        else if (view !== "map") { setView("map"); invalidateSize(); }
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [aiOpen, riskOpen, view, invalidateSize]);

  const isMap = view === "map";
  const isRiskView = view === "risk";

  return (
    <div className="app-root">
      {/* Barre du haut */}
      <TopBar
        onSearch={handleSearch}
        onOpenMenu={() => {}}
        onOpenRisk={() => setRiskOpen(true)}
        onOpenAi={() => setAiOpen(true)}
        onAnnounce={() => showToast("Données hotspots : VIIRS 375 m – NASA FIRMS (dernières 24 h)")}
        onContact={() => window.open("https://earthdata.nasa.gov/contact", "_blank")}
      />

      {/* Zone principale */}
      {(isMap || isRiskView) && (
        <div style={{ position: "absolute", inset: "var(--hh) 0 0", zIndex: 100 }}>
          <MapView
            activeBase="esri"
            showRisk={showRiskOnMap && showRisk}
            riskThreshold={riskThreshold / 100}
            riskData={riskData}
            mapRef={mapRef}
          />
        </div>
      )}

      {view === "overview" && (
        <div style={{ position: "absolute", inset: "var(--hh) 0 0", zIndex: 1300, background: "var(--ash)" }}>
          <OverviewView />
        </div>
      )}
      {view === "calendar" && (
        <div style={{ position: "absolute", inset: "var(--hh) 0 0", zIndex: 1300, background: "var(--ash)" }}>
          <CalendarView />
        </div>
      )}
      {view === "jobs" && (
        <div style={{ position: "absolute", inset: "var(--hh) 0 0", zIndex: 1300, background: "var(--ash)" }}>
          <JobsView onBack={() => setView("jobs")} />
        </div>
      )}
      {view === "dq" && (
        <div style={{
          position: "absolute", inset: "var(--hh) 0 0", zIndex: 1300,
          background: "rgb(14 42 37/.62)", backdropFilter: "blur(6px)",
          display: "flex", alignItems: "center", justifyContent: "center", padding: "1.2rem",
        }}>
          <DqView onClose={() => setView("map")} />
        </div>
      )}

      {/* Dock de navigation */}
      {(isMap || isRiskView) && (
        <div style={{
          position: "absolute", left: "50%", bottom: "max(1rem,env(safe-area-inset-bottom))",
          transform: "translateX(-50%)", zIndex: 1450,
        }}>
          <DockNav active={isRiskView ? "risk" : view} onSelect={handleNavSelect} />
        </div>
      )}

      {/* Sphère flottante — ouvre l'assistant IA */}
      {(isMap || isRiskView) && (
        <RiskSphere
          open={aiOpen}
          onClick={() => setAiOpen((v) => !v)}
          hasData={!!riskData}
        />
      )}

      {/* Panneau risque */}
      {(isMap || isRiskView) && (
        <div style={{ position: "absolute", inset: 0, zIndex: 1060, pointerEvents: riskOpen ? "auto" : "none" }}>
          <RiskPanel
            open={riskOpen}
            onClose={() => setRiskOpen(false)}
          />
        </div>
      )}

      {/* Panneau IA */}
      {(isMap || isRiskView) && (
        <AiPanel
          open={aiOpen}
          onClose={() => setAiOpen(false)}
          onSend={handleAiSend}
        />
      )}

      {/* Toast */}
      <Toast message={toastMsg} onDone={hideToast} />
    </div>
  );
}
