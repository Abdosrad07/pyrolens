import { useMemo } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import StatCard from "../components/StatCard.jsx";
import { fmt } from "../data.js";

const SENSOR_KIND_LABELS = {
  modis: "MODIS (Terra + Aqua)",
  viirs: "VIIRS S-NPP",
};

const QUICK_LINKS = [
  { hash: "harmonization-new", title: "Lancer une expérience", desc: "Harmonization Lab — création en 5 étapes" },
  { hash: "fire-calendar", title: "Calendrier des feux", desc: "Évolution temporelle des observations" },
  { hash: "data", title: "Catalogue des données", desc: "Jeux source et artefacts dérivés" },
  { hash: "methodology", title: "Méthodologie", desc: "Questions, clés d'ensembles, limites" },
];

function OriginBanner({ origin, generatedAt }) {
  const stamp = generatedAt ? ` · artefacts du ${generatedAt.slice(0, 10)}` : "";
  if (origin === "synthetic_fixture") {
    return (
      <div className="banner warn">
        <strong>Origine des données : échantillon synthétique de démonstration{stamp}</strong>
        Les données NASA réelles n'ont pas pu être acquises dans cet environnement
        (blocages HTTP documentés ci-dessous). Tous les chiffres calculés ici proviennent
        d'un échantillon synthétique : ils valident le pipeline, ils ne sont **pas** des
        mesures du Cameroun. Aucune valeur antérieure v0.3 n'est présentée comme recalculée.
      </div>
    );
  }
  return (
    <div className="banner info">
      <strong>Origine des données : {origin}{stamp}</strong>
      Valeurs calculées par le pipeline sur les données listées dans l'inventaire.
    </div>
  );
}

function statusPill(status) {
  const norm = String(status ?? "")
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "");

  if (norm === "ok") return <span className="pill ok">ok</span>;
  if (norm === "bloque" || norm === "blocked")
    return <span className="pill blocked">bloqué</span>;
  return <span className="pill ref">{status}</span>;
}

// ---------- carte dégradée (indices de cellules, pas de coordonnées GPS) ----

function SpatialGrid({ cells }) {
  // cells : lignes de baselines.spatial (config. primaire, 2 paires) — indices
  // de cellules d'une grille uniforme ; la position relative est fidèle,
  // l'échelle ne l'est pas. Agrégation par cellule : les comptages des deux
  // paires sont cumulés (un capteur peut figurer dans les deux paires).
  const aggregated = useMemo(() => {
    const map = new Map();
    for (const c of cells) {
      const key = `${c.cell_i},${c.cell_j}`;
      const cur = map.get(key) || { cell_i: c.cell_i, cell_j: c.cell_j, a_count: 0, b_count: 0 };
      cur.a_count += c.a_count || 0;
      cur.b_count += c.b_count || 0;
      map.set(key, cur);
    }
    return [...map.values()];
  }, [cells]);

  const geom = useMemo(() => {
    if (!aggregated.length) return null;
    const iis = aggregated.map((c) => c.cell_i);
    const jjs = aggregated.map((c) => c.cell_j);
    const iMin = Math.min(...iis);
    const iMax = Math.max(...iis);
    const jMin = Math.min(...jjs);
    const jMax = Math.max(...jjs);
    const w = iMax - iMin + 1;
    const h = jMax - jMin + 1;
    const maxVal = Math.max(...aggregated.map((c) => c.a_count + c.b_count), 1);
    return { iMin, jMin, jMax, w, h, maxVal };
  }, [aggregated]);

  if (!geom) return null;
  const cell = 12;
  const W = geom.w * cell;
  const H = geom.h * cell;

  return (
    <svg
      viewBox={`0 0 ${W} ${H}`}
      style={{ width: "100%", height: "auto", display: "block" }}
      role="img"
      aria-label="Distribution spatiale des cellules actives"
    >
      {aggregated.map((c, i) => {
        const total = c.a_count + c.b_count;
        const alpha = 0.08 + 0.72 * (total / geom.maxVal);
        return (
          <rect
            key={i}
            x={(c.cell_i - geom.iMin) * cell}
            y={(geom.jMax - c.cell_j) * cell}
            width={cell - 1}
            height={cell - 1}
            rx={1.5}
            fill={`rgba(255, 122, 51, ${alpha.toFixed(3)})`}
          >
            <title>{`cellule ${c.cell_i},${c.cell_j} — comptages cumulés A: ${fmt(c.a_count)} · B: ${fmt(c.b_count)}`}</title>
          </rect>
        );
      })}
    </svg>
  );
}

// ---------- vue ----------------------------------------------------------------

export default function Overview({ data }) {
  const exec = data.execution || {};
  const steps = exec.steps || [];
  const blockers = exec.blockers || [];
  const inv = data.inventory;
  const dl = data.downloads;
  const audit = data.audit || {};
  const baselines = data.baselines || {};

  const nOk = steps.filter((s) => s.status === "ok").length;
  const origin = audit.data_origin || "—";

  // ---------- statistiques d'exploration (artefacts) ----------
  const fileStats = useMemo(() => {
    const files = audit.files || [];
    const bySensor = {};
    let nRecords = 0;
    let nAnalysable = 0;
    for (const f of files) {
      const s = (bySensor[f.sensor] ||= { files: 0, n_records: 0, n_rows_analysable: 0 });
      s.files += 1;
      s.n_records += f.n_records || 0;
      s.n_rows_analysable += f.n_rows_analysable || 0;
      nRecords += f.n_records || 0;
      nAnalysable += f.n_rows_analysable || 0;
    }
    return { bySensor, nRecords, nAnalysable, nFiles: files.length };
  }, [audit]);

  const spatialCells = useMemo(() => {
    const primary = baselines.primary || {};
    return (baselines.spatial || []).filter(
      (r) => r.grid_deg === primary.grid_deg && r.window_days === primary.window_days
    );
  }, [baselines]);

  const volumeSeries = useMemo(() => {
    const vm = audit.volumes_by_month || {};
    const sensors = new Set();
    const map = new Map();
    for (const [key, value] of Object.entries(vm)) {
      const [sensor, month] = key.split("|");
      sensors.add(sensor);
      const cur = map.get(month) || { month };
      cur[sensor] = (cur[sensor] || 0) + value;
      map.set(month, cur);
    }
    return {
      rows: [...map.values()].sort((a, b) => (a.month < b.month ? -1 : 1)),
      sensors: [...sensors].sort(),
    };
  }, [audit]);

  const period =
    exec.period_start && exec.period_end
      ? `${exec.period_start} → ${exec.period_end}`
      : inv?.period?.start && inv?.period?.end
        ? `${inv.period.start} → ${inv.period.end}`
        : "2013-01-01 → 2020-12-31";

  const frp = audit.frp_stats || {};

  return (
    <div>
      <h2 className="page-title">Overview</h2>
      <p className="page-sub">
        PyroLens — comparaison des détections de points chauds MODIS Terra, MODIS
        Aqua et VIIRS S-NPP sur le Cameroun (2013-2020). Chaque chiffre affiché
        provient des artefacts horodatés du pipeline ; les limites
        d'interprétation sont rappelées sur chaque écran.
      </p>

      <OriginBanner origin={origin} generatedAt={audit.generated_at} />

      {/* ---------- indicateurs d'exploration ---------- */}
      <div className="cards">
        <StatCard
          title="Lignes analysables"
          value={fileStats.nAnalysable}
          unit="observations"
          description="dans l'emprise, hors ambiguës"
        />
        <StatCard
          title="Fichiers audités"
          value={fileStats.nFiles}
          unit="fichiers"
          description={Object.keys(fileStats.bySensor)
            .map((s) => SENSOR_KIND_LABELS[s] || s)
            .join(" + ")}
        />
        <StatCard
          title="Jours avec enregistrements"
          value={audit.n_distinct_days_with_records ?? "—"}
          unit="jours"
          description="capteur-jours distincts"
        />
        <StatCard
          title="Cellules actives"
          value={spatialCells.length || "—"}
          unit="cellules"
          description="configuration primaire (0,25° × 8 j)"
        />
        <StatCard
          title="FRP moyen / max"
          value={frp.mean != null ? `${fmt(frp.mean, 1)} / ${fmt(frp.max, 1)}` : "—"}
          unit="MW"
          description="puissance radiative, artefact audit"
        />
      </div>

      {/* ---------- répartition par capteur ---------- */}
      {Object.keys(fileStats.bySensor).length > 0 && (
        <div className="panel">
          <h3>
            Observations par capteur
            <span className="hint">lignes auditées — MODIS regroupe Terra et Aqua</span>
          </h3>
          <div className="table-wrap">
            <table className="data">
              <thead>
                <tr>
                  <th>Capteur</th>
                  <th>Fichiers</th>
                  <th>Lignes</th>
                  <th>Analysables</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(fileStats.bySensor).map(([sensor, s]) => (
                  <tr key={sensor}>
                    <td className="txt">
                      <strong>{SENSOR_KIND_LABELS[sensor] || sensor}</strong>
                    </td>
                    <td>{fmt(s.files)}</td>
                    <td>{fmt(s.n_records)}</td>
                    <td>{fmt(s.n_rows_analysable)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* ---------- distribution spatiale (mode dégradé) ---------- */}
      <div className="panel">
        <h3>
          Distribution spatiale des cellules actives
          <span className="hint">indices de grille — pas une carte géographique</span>
        </h3>
        {spatialCells.length === 0 ? (
          <p className="muted">
            Distribution spatiale indisponible : l'artefact <span className="mono">baselines.json</span> ne
            publie pas les coordonnées GPS des cellules, seulement leurs indices de grille.
            Mode dégradé explicite — aucune position n'est inventée.
          </p>
        ) : (
          <>
            <SpatialGrid cells={spatialCells} />
            <p className="legend-note">
              Chaque case = une cellule de la grille d'analyse (maille 0,25°, fenêtre 8 j,
              configuration primaire) ; l'intensité suit les comptages cumulés des deux
              paires (a_count + b_count — un capteur présent dans deux paires est donc
              compté deux fois, décompte indicatif). La position relative est fidèle,
              l'échelle géographique n'est pas représentée : les coordonnées publiées
              sont des indices de cellules, pas des longitude/latitude.
            </p>
          </>
        )}
      </div>

      {/* ---------- volumes mensuels par capteur ---------- */}
      {volumeSeries.rows.length > 0 && (
        <div className="panel">
          <h3>
            Volumes mensuels d'observations
            <span className="hint">par capteur — toutes années confondues</span>
          </h3>
          <div className="chart-box tall">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={volumeSeries.rows}>
                <CartesianGrid strokeDasharray="3 3" stroke="#23303f" />
                <XAxis dataKey="month" tick={{ fill: "#8ba0b8", fontSize: 11 }} />
                <YAxis tick={{ fill: "#8ba0b8", fontSize: 11 }} />
                <Tooltip
                  contentStyle={{ background: "#182231", border: "1px solid #23303f" }}
                  formatter={(v) => fmt(v)}
                />
                <Legend />
                {volumeSeries.sensors.map((s, i) => (
                  <Line
                    key={s}
                    type="monotone"
                    dataKey={s}
                    name={SENSOR_KIND_LABELS[s] || s}
                    stroke={["#ff7a33", "#35c8c0", "#5aa7ff", "#f5c542"][i % 4]}
                    strokeWidth={1.5}
                    dot={false}
                  />
                ))}
              </LineChart>
            </ResponsiveContainer>
          </div>
          <p className="legend-note">
            Comptages issus de l'audit (volumes par capteur et mois). La saisonnalité
            visible est celle des passages satellitaires et des conditions
            d'observation — pas une mesure d'activité de feu au sol.
          </p>
        </div>
      )}

      {/* ---------- accès rapide ---------- */}
      <div className="panel">
        <h3>Accès rapide</h3>
        <div className="cards">
          {QUICK_LINKS.map((l) => (
            <a
              key={l.hash}
              href={`#${l.hash}`}
              className="card"
              style={{ textDecoration: "none", color: "inherit", cursor: "pointer" }}
            >
              <div className="k">{l.title}</div>
              <div className="d">{l.desc}</div>
            </a>
          ))}
        </div>
      </div>

      {/* ---------- exécution du pipeline (écran « Synthèse » historique) ---------- */}
      <h3 className="page-title" style={{ fontSize: 20, marginTop: 34 }}>
        Exécution du pipeline
        <span className="hint" style={{ fontSize: 12, fontWeight: 400 }}>
          journalisé dans reports/logs/ — état réel de la chaîne {exec.project_version || "pyrolens"}
        </span>
      </h3>

      <div className="cards">
        <div className="card">
          <div className="k">Étapes exécutées</div>
          <div className="v">
            {nOk}
            <span style={{ fontSize: 15, color: "var(--muted)" }}> / {steps.length}</span>
          </div>
          <div className="d">statut « ok »</div>
        </div>
        <div className="card">
          <div className="k">Blocages documentés</div>
          <div className="v" style={{ color: blockers.length ? "var(--red)" : undefined }}>
            {blockers.length}
          </div>
          <div className="d">accès données réelles</div>
        </div>
        <div className="card">
          <div className="k">Période cible</div>
          <div className="v small mono">
            {exec.period_start} → {exec.period_end}
          </div>
          <div className="d">conforme au plan</div>
        </div>
        <div className="card">
          <div className="k">Origine des données</div>
          <div className="v small">{origin}</div>
          <div className="d">étiqueté dans chaque JSON</div>
        </div>
        <div className="card">
          <div className="k">Fichiers téléchargés</div>
          <div className="v">{dl?.entry_count ?? "—"}</div>
          <div className="d">manifeste SHA-256</div>
        </div>
      </div>

      <div className="panel">
        <h3>
          Étapes du pipeline
          <span className="hint">journalisé dans reports/logs/</span>
        </h3>
        <div className="table-wrap">
          <table className="data">
            <thead>
              <tr>
                <th>Étape</th>
                <th>Statut</th>
                <th>Preuve / détail</th>
                <th>Horodatage</th>
              </tr>
            </thead>
            <tbody>
              {steps.map((s, i) => (
                <tr key={i}>
                  <td className="txt">
                    <strong>{s.step}</strong>
                  </td>
                  <td>{statusPill(s.status)}</td>
                  <td className="txt">{s.detail}</td>
                  <td className="muted">{(s.at || "").slice(0, 19)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {blockers.length > 0 && (
        <div className="panel">
          <h3>
            Blocages d'accès aux données
            <span className="hint">aucun contournement d'authentification</span>
          </h3>
          {blockers.map((b, i) => (
            <div className="blocker" key={i}>
              <div className="what">
                {b.what}{" "}
                {b.http_status ? <span className="pill blocked">HTTP {b.http_status}</span> : null}
              </div>
              <div className="detail">{b.detail}</div>
              <div className="action">
                <strong>Action attendue :</strong> {b.action}
              </div>
            </div>
          ))}
        </div>
      )}

      {inv && (
        <div className="panel">
          <h3>
            Inventaire FIRMS / CMR
            <span className="hint">vérifié avant tout téléchargement massif</span>
          </h3>
          <p className="muted small" style={{ marginTop: 0 }}>
            Source : {inv.source} — {inv.base_url} · période vérifiée {inv.period?.start} →{" "}
            {inv.period?.end}
            {inv.bbox_note ? ` · ${inv.bbox_note}` : ""}
          </p>
          <div className="table-wrap">
            <table className="data">
              <thead>
                <tr>
                  <th>Capteur</th>
                  <th>Short name (CMR)</th>
                  <th>Version retenue</th>
                  <th>Années disponibles</th>
                  <th>Granules 2019 (bbox)</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(inv.sensors || {}).map(([key, s]) => (
                  <tr key={key}>
                    <td className="txt">
                      <strong>{s.label || key}</strong>
                    </td>
                    <td>{s.short_name}</td>
                    <td>{s.version_used || s.configured_version}</td>
                    <td>
                      {Array.isArray(s.years)
                        ? `${s.years.length} ans (${s.years[0]}–${s.years[s.years.length - 1]})`
                        : "—"}
                    </td>
                    <td>{fmt(s.sample_granules_2019)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {dl && dl.by_status && dl.by_status.length > 0 && (
        <div className="panel">
          <h3>
            Manifeste de téléchargement (agrégat)
            <span className="hint">{dl.entry_count} entrées — détail complet dans downloads.json sur disque</span>
          </h3>
          <div className="table-wrap">
            <table className="data">
              <thead>
                <tr>
                  <th>Statut</th>
                  <th>Entrées</th>
                  <th>Acquises</th>
                  <th>Détail</th>
                </tr>
              </thead>
              <tbody>
                {dl.by_status.map((s, i) => (
                  <tr key={i}>
                    <td className="txt">{s.status}</td>
                    <td>{fmt(s.count)}</td>
                    <td>{s.acquired ? fmt(s.count) : "0"}</td>
                    <td className="txt muted">
                      {s.status === "blocked_earthdata_login"
                        ? "Clés Earthdata requises (D4)"
                        : s.status === "blocked_missing_credential"
                        ? "Clé FIRMS requise"
                        : s.status === "deferred"
                        ? "Budget de commande atteint — repris à l'exécution suivante"
                        : s.status === "already_present"
                        ? "Déjà présent sur disque"
                        : s.status === "downloaded"
                        ? "Téléchargé avec succès"
                        : s.status === "http_error"
                        ? "Erreur HTTP — consultez downloads.json"
                        : s.status === "error"
                        ? "Erreur de traitement — consultez downloads.json"
                        : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {dl.coverage_products_acquired === false && (
            <p className="muted small">
              Produits de couverture/nuages non acquis : observabilité par défaut « inconnue ».
            </p>
          )}
        </div>
      )}
    </div>
  );
}
