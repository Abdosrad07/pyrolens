import { useEffect, useState } from "react";
import { loadAll } from "./data.js";
import Landing from "./views/Landing.jsx";
import Auth from "./Auth.jsx";
import Overview from "./views/Overview.jsx";
import Audit from "./views/Audit.jsx";
import Baselines from "./views/Baselines.jsx";
import Observability from "./views/Observability.jsx";
import Report from "./views/Report.jsx";
import Figures from "./views/Figures.jsx";
import HarmonizationList from "./views/HarmonizationList.jsx";
import HarmonizationNew from "./views/HarmonizationNew.jsx";
import HarmonizationDetail from "./views/HarmonizationDetail.jsx";
import DataCatalog from "./views/DataCatalog.jsx";
import DatasetDetail from "./views/DatasetDetail.jsx";
import Methodology from "./views/Methodology.jsx";
import FireCalendar from "./views/FireCalendar.jsx";

const VIEWS = [
  { id: "overview", label: "Overview" },
  { id: "audit", label: "Audit des données" },
  { id: "baselines", label: "Baselines de concordance" },
  { id: "observability", label: "Observabilité (4 états)" },
  { id: "report", label: "Rapport scientifique" },
  { id: "figures", label: "Figures" },
];

const NEW_VIEWS = [
  { id: "fire-calendar", label: "Calendrier des feux" },
  { id: "harmonization", label: "Harmonization Lab" },
  { id: "data", label: "Données" },
  { id: "methodology", label: "Méthodologie" },
];

const SESSION_KEY = "pyrolens.session";

const ALL_VIEW_IDS = new Set([
  "landing",
  "auth",
  "overview",
  "audit",
  "baselines",
  "observability",
  "report",
  "figures",
  "fire-calendar",
  "harmonization",
  "harmonization-new",
  "data",
  "methodology",
]);

/** Traduit un hash d'URL (#harmonization-abc, #data-xyz…) en id de vue. */
function hashToView(hash) {
  const h = String(hash || "").replace(/^#\/?/, "");
  if (!h) return null;
  if (h.startsWith("harmonization-") || h.startsWith("data-")) return h;
  return ALL_VIEW_IDS.has(h) ? h : null;
}

function readSession() {
  try {
    return sessionStorage.getItem(SESSION_KEY) === "1";
  } catch {
    return false;
  }
}

function writeSession(on) {
  try {
    if (on) sessionStorage.setItem(SESSION_KEY, "1");
    else sessionStorage.removeItem(SESSION_KEY);
  } catch {
    /* stockage indisponible : la session reste en mémoire */
  }
}

export default function App() {
  const [data, setData] = useState(null);
  const [view, setView] = useState(() => hashToView(window.location.hash) || "landing");
  const [authed, setAuthed] = useState(readSession);
  const [returnTo, setReturnTo] = useState("overview");

  useEffect(() => {
    let alive = true;
    loadAll().then((d) => alive && setData(d));
    return () => {
      alive = false;
    };
  }, []);

  // Les vues modules naviguent via window.location.hash : écouter le hash.
  useEffect(() => {
    function onHash() {
      const target = hashToView(window.location.hash);
      if (target) go(target);
    }
    window.addEventListener("hashchange", onHash);
    return () => window.removeEventListener("hashchange", onHash);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [authed]);

  // Les vues du pipeline exigent une session ; on mémorise la destination.
  function go(target) {
    let dest = target;
    if (target !== "landing" && target !== "auth" && !authed) {
      setReturnTo(target);
      dest = "auth";
    }
    setView(dest);
    window.location.hash = dest === "landing" ? "" : dest;
  }

  function enter(target = "overview") {
    setAuthed(true);
    writeSession(true);
    setView(target);
  }

  function leave() {
    setAuthed(false);
    writeSession(false);
    setView("landing");
  }

  if (!data) {
    return (
      <div className="app">
        <main className="main">
          <div className="loading">Chargement des artefacts du pipeline…</div>
        </main>
      </div>
    );
  }

  const period =
    data.execution?.period_start && data.execution?.period_end
      ? `${data.execution.period_start} → ${data.execution.period_end}`
      : "2013-01-01 → 2020-12-31";
  const generatedAt =
    data.audit?.generated_at || data.baselines?.generated_at || "";

  return (
    <div className="app">
      <aside className="sidebar">
        <div className="brand">
          <h1>PyroLens</h1>
          <div className="sub">Phase 2 · MODIS / VIIRS</div>
          <div className="period">{period}</div>
        </div>
        <nav className="nav">
          <div className="nav-group">Navigation</div>
          <button
            className={view === "landing" ? "active" : ""}
            onClick={() => go("landing")}
          >
            ← Accueil
          </button>
          <div className="nav-group">Rapports</div>
          {VIEWS.map((v) => (
            <button
              key={v.id}
              className={view === v.id ? "active" : ""}
              onClick={() => go(v.id)}
            >
              {v.label}
            </button>
          ))}
          <div className="nav-group">Modules</div>
          {NEW_VIEWS.map((v) => (
            <button
              key={v.id}
              className={view === v.id ? "active" : ""}
              onClick={() => go(v.id)}
            >
              {v.label}
            </button>
          ))}
        </nav>
        <div className="foot">
          {authed ? (
            <>
              session : connecté
              <br />
              <button className="linkish" onClick={leave}>
                quitter la session
              </button>
            </>
          ) : (
            <>
              session : invitée
              <br />
              <button className="linkish" onClick={() => go("auth")}>
                se connecter
              </button>
            </>
          )}
          <br />
          {data.execution?.project_version
            ? `pipeline ${data.execution.project_version}`
            : "pipeline v0.2.0"}
          <br />
          {generatedAt ? `artefacts ${generatedAt.slice(0, 16)}` : ""}
        </div>
      </aside>

      <main className="main">
        {view === "landing" && (
          <Landing
            data={data}
            onStart={() => go("auth")}
            onDemo={(target) => enter(target || "overview")}
          />
        )}
        {view === "auth" && (
          <Auth
            returnTo={returnTo}
            onAuthed={(t) => enter(t || "overview")}
            onCancel={() => setView("landing")}
            onDemo={() => enter("overview")}
          />
        )}
        {view === "overview" && <Overview data={data} />}
        {view === "audit" && <Audit data={data} />}
        {view === "baselines" && <Baselines data={data} />}
        {view === "observability" && <Observability data={data} />}
        {view === "report" && <Report data={data} />}
        {view === "figures" && <Figures data={data} />}
        {view === "fire-calendar" && <FireCalendar />}
        {view === "harmonization" && <HarmonizationList data={data} />}
        {view === "harmonization-new" && <HarmonizationNew />}
        {view.startsWith("harmonization-") && <HarmonizationDetail jobId={view.replace("harmonization-", "")} />}
        {view === "data" && <DataCatalog data={data} />}
        {view.startsWith("data-") && <DatasetDetail datasetId={view.replace("data-", "")} />}
        {view === "methodology" && <Methodology />}
      </main>
    </div>
  );
}
