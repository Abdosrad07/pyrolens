/**
 * App — composant racine de PyroLens.
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
import HamburgerMenu from "./components/HamburgerMenu.jsx";
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
import { I18nProvider, useI18n } from "./i18n/index.jsx";

const VIEWS = {
  map: { fr: "Carte", en: "Map" },
  overview: { fr: "Aperçu", en: "Overview" },
  calendar: { fr: "Calendrier", en: "Calendar" },
  jobs: { fr: "Jobs", en: "Jobs" },
  dq: { fr: "Qualité des données", en: "Data quality" },
  risk: { fr: "Risque de feu", en: "Fire risk" },
};

function InnerApp() {
  const { t, lang, toggle } = useI18n();
  const [view, setView] = useState("map");
  const [aiOpen, setAiOpen] = useState(false);
  const [riskOpen, setRiskOpen] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const [toastMsg, setToastMsg] = useState(null);
  const [showRisk, setShowRisk] = useState(true);
  const [riskThreshold, setRiskThreshold] = useState(0);

  const { mapRef, flyToView, flyToCoords, invalidateSize } = useMap();
  const { riskData, loading: riskLoading, reload: reloadRisk, origin, generatedAt, metrics, cellsCount, highCells } =
    useRiskData();
  const api = useApi();

  useEffect(() => {
    if (!riskData) reloadRisk();
  }, []);

  const showRiskOnMap = showRisk && (view === "map" || view === "risk");

  const showToast = useCallback((key) => setToastMsg(t(key)), [t]);
  const hideToast = useCallback(() => setToastMsg(null), []);

  const handleSearch = useCallback(async (q) => {
    showToast("toast.searching");
    const res = await api.geocode(q);
    if (res) {
      setView("map");
      flyToCoords(res.lat, res.lon, 8);
      showToast("toast.located");
    } else {
      showToast("toast.notFound");
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
      // « Risque » ramène sur la carte et ouvre le panneau de risque.
      setView("map");
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
      <TopBar
        onSearch={handleSearch}
        onOpenMenu={() => setMenuOpen((v) => !v)}
        onOpenRisk={() => setRiskOpen(true)}
        onOpenAi={() => setAiOpen(true)}
        onAnnounce={() => showToast("toast.announce")}
        onContact={() => window.open("https://earthdata.nasa.gov/contact", "_blank")}
        onToggleLang={toggle}
      />

      <HamburgerMenu
        open={menuOpen}
        onClose={() => setMenuOpen(false)}
        onSelect={handleNavSelect}
        active={view}
      />

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
          <OverviewView onBack={() => { setView("map"); invalidateSize(); }} />
        </div>
      )}
      {view === "calendar" && (
        <div style={{ position: "absolute", inset: "var(--hh) 0 0", zIndex: 1300, background: "var(--ash)" }}>
          <CalendarView onBack={() => { setView("map"); invalidateSize(); }} />
        </div>
      )}
      {view === "jobs" && (
        <div style={{ position: "absolute", inset: "var(--hh) 0 0", zIndex: 1300, background: "var(--ash)" }}>
          <JobsView onBack={() => { setView("map"); invalidateSize(); }} />
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

      {/* Dock de navigation — visible sur toutes les vues */}
      <div style={{
        position: "absolute", left: "50%", bottom: "max(1rem,env(safe-area-inset-bottom))",
        transform: "translateX(-50%)", zIndex: 1450,
      }}>
        <DockNav active={isRiskView ? "risk" : view} onSelect={handleNavSelect} />
      </div>

      {/* Sphère flottante — ouvre l'assistant IA (toutes vues) */}
      <RiskSphere
        open={aiOpen}
        onClick={() => setAiOpen((v) => !v)}
        hasData={!!riskData}
      />

      {(isMap || isRiskView) && (
        <div style={{ position: "absolute", inset: 0, zIndex: 1060, pointerEvents: riskOpen ? "auto" : "none" }}>
          <RiskPanel
            open={riskOpen}
            onClose={() => setRiskOpen(false)}
          />
        </div>
      )}

      {/* Panneau IA — accessible depuis toutes les vues */}
      <AiPanel
        open={aiOpen}
        onClose={() => setAiOpen(false)}
        onSend={handleAiSend}
      />

      <Toast message={toastMsg} onDone={hideToast} />
    </div>
  );
}

export default function App() {
  return (
    <I18nProvider>
      <InnerApp />
    </I18nProvider>
  );
}
