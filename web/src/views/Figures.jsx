const FIGURES = [
  { file: "anomalies_by_category.png", caption: "Anomalies par catégorie (comptées par l'audit)" },
  { file: "volumes_by_month.png", caption: "Volumes de détections par mois et par capteur" },
  { file: "jaccard_monthly.png", caption: "Évolution mensuelle du Jaccard par paire" },
  { file: "jaccard_sensitivity.png", caption: "Sensibilité du Jaccard aux grilles et fenêtres" },
  { file: "spatial_distribution.png", caption: "Distribution spatiale des désaccords (cellules de grille)" },
  { file: "observability_states.png", caption: "Répartition des 4 états d'observabilité" },
];

export default function Figures() {
  return (
    <div>
      <h2 className="page-title">Figures</h2>
      <p className="page-sub">
        PNG produits par Matplotlib (<span className="mono">pyrolens figures</span>), servis
        depuis <span className="mono">web/public/artifacts/figures/</span>.
      </p>
      <div className="fig-grid">
        {FIGURES.map((f) => (
          <figure className="fig" key={f.file}>
            <img
              src={`/artifacts/figures/${f.file}`}
              alt={f.caption}
              loading="lazy"
              onError={(e) => {
                e.currentTarget.style.display = "none";
              }}
            />
            <figcaption>
              {f.file} — {f.caption}
            </figcaption>
          </figure>
        ))}
      </div>
    </div>
  );
}
