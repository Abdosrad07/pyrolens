import { fmt, SENSOR_LABELS } from "../data.js";

const MODULES = [
  {
    id: "overview",
    title: "Synthèse d'exécution",
    desc: "L'état réel de la chaîne, étape par étape : chaque « ok » est un artefact produit, chaque blocage est documenté sans être déguisé en succès.",
    tag: "provenance",
  },
  {
    id: "audit",
    title: "Audit des données",
    desc: "Inventaire FIRMS / CMR, manifeste SHA-256 des téléchargements et origine exacte des fichiers utilisés par le pipeline.",
    tag: "intégrité",
  },
  {
    id: "baselines",
    title: "Baselines de concordance",
    desc: "Matrices de concordance inter-capteurs (Terra, Aqua, VIIRS S-NPP) sur mailles normalisées, fenêtres temporelles 1 à 16 jours.",
    tag: "calcul",
  },
  {
    id: "observability",
    title: "Observabilité (4 états)",
    desc: "Détection d'anomalies par capteur et par période, avec les quatre états normalisés du cadre de travail et leurs justifications.",
    tag: "contrôle",
  },
  {
    id: "report",
    title: "Rapport scientifique",
    desc: "Rapport Markdown généré : méthodologie, chiffres de la littérature séparés des valeurs calculées, limites assumées.",
    tag: "réconciliation",
  },
  {
    id: "figures",
    title: "Figures",
    desc: "Série temporelle et cartes de densité exportées depuis les artefacts, jamais dessinées à la main.",
    tag: "sorties",
  },
];

const PIPELINE = [
  { k: "01", t: "Inventaire", d: "Granules CMR vérifiés avant tout téléchargement massif." },
  { k: "02", t: "Acquisition", d: "Chaque fichier horodaté, SHA-256 calculé, échec conservé tel quel." },
  { k: "03", t: "Normalisation", d: "Schéma commun MODIS / VIIRS, unités et seuils alignés." },
  { k: "04", t: "Concordance", d: "Comparaison croisée sur mailles et fenêtres paramétrées." },
  { k: "05", t: "Réconciliation", d: "Écarts vs littérature calculés, jamais surchargés à la main." },
  { k: "06", t: "Rapport", d: "Markdown + figures régénérés à chaque exécution." },
];

function originPill(origin) {
  if (origin === "synthetic_fixture") return <span className="pill ref">fixture synthétique</span>;
  if (origin === "nasa_firms") return <span className="pill ok">NASA FIRMS réelles</span>;
  return <span className="pill calc">{origin || "—"}</span>;
}

export default function Landing({ data, onStart, onDemo }) {
  const exec = data?.execution || {};
  const steps = exec.steps || [];
  const blockers = exec.blockers || [];
  const nOk = steps.filter((s) => s.status === "ok").length;
  const origin = data?.audit?.data_origin || "—";
  const dl = data?.downloads;
  const period =
    exec.period_start && exec.period_end
      ? `${exec.period_start} → ${exec.period_end}`
      : "2013-01-01 → 2020-12-31";
  const sensors = Object.entries(data?.inventory?.sensors || {});

  return (
    <div className="landing">
      {/* ---------------- hero ---------------- */}
      <section className="hero">
        <div className="hero-left">
          <div className="eyebrow">Phase 2 · MODIS / VIIRS · Cameroun · 2013–2020</div>
          <h2 className="hero-title">
            La preuve avant
            <br />
            le chiffre.
          </h2>
          <p className="hero-lead">
            PyroLens est un tableau de bord d'<strong>audit scientifique</strong> pour la
            concordance des feux détectés entre MODIS (Terra, Aqua) et VIIRS S-NPP.
            Ici, aucune valeur n'est saisie à la main : chaque chiffre affiché est la
            sortie d'un artefact horodaté, reproductible, et les valeurs de la
            littérature restent séparées de celles que le pipeline recalcule.
          </p>
          <div className="hero-cta">
            <button className="btn primary" onClick={onStart}>
              Commencer
            </button>
            <button className="btn ghost" onClick={onDemo}>
              Voir la démo →
            </button>
          </div>
          <div className="hero-note">
            Lecture seule · la démo n'exige aucun compte · origine des données
            étiquetée dans chaque écran
          </div>
        </div>

        <div className="hero-right">
          <div className="hero-card">
            <div className="hero-card-head">
              <span>pipeline en direct</span>
              {originPill(origin)}
            </div>
            <div className="hero-metrics">
              <div className="hm">
                <div className="hm-v">
                  {nOk}
                  <span> / {steps.length}</span>
                </div>
                <div className="hm-k">étapes attestées</div>
              </div>
              <div className="hm">
                <div className="hm-v" style={{ color: blockers.length ? "var(--red)" : undefined }}>
                  {blockers.length}
                </div>
                <div className="hm-k">blocages documentés</div>
              </div>
              <div className="hm">
                <div className="hm-v">{dl?.entry_count ?? "—"}</div>
                <div className="hm-k">fichiers · manifeste SHA-256</div>
              </div>
              <div className="hm">
                <div className="hm-v" style={{ fontSize: 15 }}>
                  {period}
                </div>
                <div className="hm-k">période cible</div>
              </div>
            </div>
            <div className="hero-sensors">
              {sensors.map(([key, s]) => (
                <span key={key} className="pill calc">
                  {s.label || SENSOR_LABELS[key] || s.short_name}
                </span>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* ---------------- problème ---------------- */}
      <section className="lp-sec">
        <h3 className="lp-title">Pourquoi un tableau de bord de plus ?</h3>
        <p className="lp-sub">
          Parce que la plupart des dashboards de données affichent des chiffres dont
          on ne peut plus vérifier l'origine une semaine plus tard.
        </p>
        <div className="lp-grid three">
          <div className="lp-item">
            <div className="lp-num">01</div>
            <h4>Des chiffres sans piste d'audit</h4>
            <p>
              Une valeur copiée d'un notebook ou d'un tableur ne dit ni quelle
              version du fichier elle utilise, ni à quand remonte son calcul.
              PyroLens attache chaque étape à son artefact et son horodatage.
            </p>
          </div>
          <div className="lp-item">
            <div className="lp-num">02</div>
            <h4>Deux capteurs, deux résolutions</h4>
            <p>
              MODIS (1 km) et VIIRS S-NPP (375 m) ne voient pas le même feu : sans
              maille ni fenêtre communes, la « concordance » est un choix caché.
              Ici, la maille et la fenêtre sont des paramètres explicites.
            </p>
          </div>
          <div className="lp-item">
            <div className="lp-num">03</div>
            <h4>L'origine des données masquée</h4>
            <p>
              Blocages d'accès NASA, échantillons de substitution : la tentation
              est grande de présenter un substitut comme une mesure. PyroLens
              affiche l'origine en permanence et refuse de masquer un échec.
            </p>
          </div>
        </div>
      </section>

      {/* ---------------- modules ---------------- */}
      <section className="lp-sec">
        <h3 className="lp-title">Six vues, un seul principe</h3>
        <p className="lp-sub">
          Chaque vue lit les artefacts produits par le pipeline ; rien n'est
          calculé côté interface.
        </p>
        <div className="lp-grid modules">
          {MODULES.map((m, i) => (
            <button className="module" key={m.id} onClick={() => onDemo(m.id)}>
              <div className="module-top">
                <span className="module-idx">{String(i + 1).padStart(2, "0")}</span>
                <span className="pill calc">{m.tag}</span>
              </div>
              <h4>{m.title}</h4>
              <p>{m.desc}</p>
              <span className="module-go">Ouvrir →</span>
            </button>
          ))}
        </div>
      </section>

      {/* ---------------- méthode ---------------- */}
      <section className="lp-sec">
        <h3 className="lp-title">La chaîne, du satellite au rapport</h3>
        <div className="pipeline">
          {PIPELINE.map((p) => (
            <div className="pipe-step" key={p.k}>
              <div className="pipe-k">{p.k}</div>
              <div className="pipe-t">{p.t}</div>
              <div className="pipe-d">{p.d}</div>
            </div>
          ))}
        </div>
        <div className="banner info" style={{ marginTop: 18 }}>
          <strong>Règle non négociable : la littérature n'est jamais recopiée dans nos calculs.</strong>
          Les valeurs de référence de la littérature sont listées à part, et tout écart
          est recalculé depuis les artefacts — c'est la décision D1 du projet.
        </div>
      </section>

      {/* ---------------- transparence ---------------- */}
      <section className="lp-sec">
        <div className={origin === "synthetic_fixture" ? "banner warn" : "banner info"}>
          <strong>Origine des données affichée en clair : {origin}</strong>
          {origin === "synthetic_fixture"
            ? " L'environnement actuel n'a pas pu acquérir les données NASA réelles (blocages HTTP documentés dans la vue Synthèse). Les chiffres de la démo proviennent d'un échantillon synthétique : ils valident le pipeline, ils ne sont pas des mesures du Cameroun."
            : " Les valeurs ont été calculées par le pipeline sur les fichiers listés dans l'audit."}{" "}
          Vous vérifiez vous-même : la vue Audit reprend le manifeste fichier par fichier.
        </div>
      </section>

      {/* ---------------- CTA final ---------------- */}
      <section className="cta-band">
        <div>
          <h3>Entrez dans le tableau de bord</h3>
          <p className="muted">
            Créez votre session pour suivre les exécutions, ou explorez
            immédiatement les artefacts publiés en démo.
          </p>
        </div>
        <div className="hero-cta">
          <button className="btn primary" onClick={onStart}>
            Commencer
          </button>
          <button className="btn ghost" onClick={onDemo}>
            Explorer la démo →
          </button>
        </div>
      </section>

      <footer className="lp-foot">
        PyroLens · Phase 2 · {fmt(steps.length)} étapes de pipeline ·
        {" "}API FastAPI en lecture seule · documentation dans <code>docs/</code>
      </footer>
    </div>
  );
}
