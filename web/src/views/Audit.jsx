import {
  Bar,
  BarChart,
  Cell,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { useMemo } from "react";
import Pagination, { usePaged } from "../components/Pagination.jsx";
import { fmt } from "../data.js";

const CAT_LABELS = {
  outside_emprise: "Hors emprise",
  malformed_row: "Ligne mal formée",
  invalid_latitude: "Latitude invalide",
  invalid_longitude: "Longitude invalide",
  invalid_date: "Date invalide",
  invalid_time: "Heure invalide",
  missing_value: "Valeur manquante",
  invalid_frp: "FRP invalide",
  invalid_confidence: "Confiance invalide",
  duplicate_row: "Doublon de ligne",
};

/** Accès tolérant aux accents des clés JSON du pipeline. */
function pick(obj, base) {
  if (!obj) return undefined;
  const norm = (s) => s.normalize("NFD").replace(/[\u0300-\u036f]/g, "");
  const key = Object.keys(obj).find((k) => norm(k) === norm(base));
  return key ? obj[key] : undefined;
}

export default function Audit({ data }) {
  const a = data.audit || {};
  const filesPage = usePaged(a.files || [], 50);
  const volRows = useMemo(
    () =>
      Object.entries(a.volumes_by_month || {})
        .map(([k, v]) => {
          const [sensor, month] = k.split("|");
          return { sensor, month, value: v };
        })
        .sort((x, y) =>
          x.month === y.month
            ? x.sensor.localeCompare(y.sensor)
            : x.month < y.month
              ? -1
              : 1
        ),
    [a]
  );
  const volPage = usePaged(volRows, 50);
  if (!data.audit)
    return <div className="loading">Artefact audit.json indisponible.</div>;

  const cats = Object.entries(a.anomalies_by_category || {})
    .map(([k, v]) => ({ name: CAT_LABELS[k] || k, value: v }))
    .filter((d) => d.value > 0)
    .sort((x, y) => y.value - x.value);
  const totalAnomalies = cats.reduce((s, d) => s + d.value, 0);
  const acct = a.row_accounting || {};

  return (
    <div>
      <h2 className="page-title">Audit des données</h2>
      <p className="page-sub">
        Contrôle de structure, de types, de dates, de coordonnées, de doublons et de trous
        temporels — séparation stricte des lignes valides, ambiguës et exclues. Aucune
        coordonnée n'est « corrigée » parce qu'une autre valeur paraîtrait plus plausible.
      </p>

      <div className="banner warn">
        <strong>
          Origine : {a.data_origin}
          {a.generated_at ? ` · artefacts du ${a.generated_at.slice(0, 10)}` : ""}
        </strong>
        {a.data_origin === "synthetic_fixture"
          ? "Échantillon synthétique de démonstration : les anomalies détectées attestent le fonctionnement du contrôle, elles ne caractérisent pas les fichiers NASA du pilote."
          : "Valeurs calculées par le pipeline sur les fichiers listés dans l'inventaire."}
      </div>

      <div className="cards">
        <div className="card">
          <div className="k">Fichiers audités</div>
          <div className="v">{a.n_files}</div>
          <div className="d">{(a.satellites || []).join(", ") || "—"}</div>
        </div>
        <div className="card">
          <div className="k">Lignes analysables</div>
          <div className="v">{fmt(acct.valides_analysables)}</div>
          <div className="d">sur {fmt(acct.lignes_bien_formees)} bien formées</div>
        </div>
        <div className="card">
          <div className="k">Lignes mal formées</div>
          <div className="v" style={{ color: pick(acct, "lignes_mal_formees") ? "var(--red)" : undefined }}>
            {fmt(pick(acct, "lignes_mal_formees"))}
          </div>
          <div className="d">numéro + motif conservés</div>
        </div>
        <div className="card">
          <div className="k">Exclues / hors emprise</div>
          <div className="v small">
            {fmt(pick(acct, "exclues_non_interpretables"))} / {fmt(pick(acct, "hors_emprise_conservees"))}
          </div>
          <div className="d">jamais reclassées</div>
        </div>
        <div className="card">
          <div className="k">Anomalies totales</div>
          <div className="v">{fmt(totalAnomalies)}</div>
          <div className="d">CSV dans reports/anomalies/</div>
        </div>
        <div className="card">
          <div className="k">FRP (min · moy · max)</div>
          <div className="v small mono">
            {a.frp_stats ? `${fmt(a.frp_stats.min, 1)} · ${fmt(a.frp_stats.mean, 1)} · ${fmt(a.frp_stats.max, 1)}` : "—"}
          </div>
          <div className="d">n = {fmt(a.frp_stats?.n)} · aucune correction FRP appliquée</div>
        </div>
      </div>

      <div className="panel">
        <h3>
          Anomalies par catégorie
          <span className="hint">comptées par le pipeline, non interpolées</span>
        </h3>
        {cats.length === 0 ? (
          <p className="muted">Aucune anomalie détectée sur les fichiers audités.</p>
        ) : (
          <>
            <div className="chart-box">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={cats} layout="vertical" margin={{ left: 20, right: 20 }}>
                  <CartesianGrid stroke="#23303f" strokeDasharray="3 3" />
                  <XAxis type="number" stroke="#8ba0b8" allowDecimals={false} />
                  <YAxis
                    type="category"
                    dataKey="name"
                    width={150}
                    stroke="#8ba0b8"
                    tick={{ fontSize: 12 }}
                  />
                  <Tooltip
                    contentStyle={{
                      background: "#131b24",
                      border: "1px solid #23303f",
                      borderRadius: 8,
                    }}
                  />
                  <Bar dataKey="value" radius={[0, 6, 6, 0]}>
                    {cats.map((_, i) => (
                      <Cell key={i} fill={i % 2 ? "#ff7a33" : "#f5c542"} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
            <div className="legend-note">
              Chaque catégorie renvoie à un CSV détaillé (numero_ligne + motif conservés) dans{" "}
              <span className="mono">reports/anomalies/</span>.
            </div>
          </>
        )}
      </div>

      <div className="panel">
        <h3>
          Répartition des lignes
          <span className="hint">comptabilité fermée : bien formées = analysables + exclues</span>
        </h3>
        <div className="table-wrap">
          <table className="data">
            <thead>
              <tr>
                <th>Classe</th>
                <th>Lignes</th>
                <th>Traitement</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td className="txt">Lignes bien formées</td>
                <td>{fmt(acct.lignes_bien_formees)}</td>
                <td className="txt muted">entrées du contrôle de structure</td>
              </tr>
              <tr>
                <td className="txt">Valides analysables</td>
                <td>{fmt(acct.valides_analysables)}</td>
                <td className="txt muted">utilisées pour grilles et baselines</td>
              </tr>
              <tr>
                <td className="txt">Hors emprise (conservées)</td>
                <td>{fmt(pick(acct, "hors_emprise_conservees"))}</td>
                <td className="txt muted">conservées, exclues des comparaisons</td>
              </tr>
              <tr>
                <td className="txt">Exclues non interprétables</td>
                <td>{fmt(pick(acct, "exclues_non_interpretables"))}</td>
                <td className="txt muted">jamais réinterprétées comme détection</td>
              </tr>
              <tr>
                <td className="txt">Lignes mal formées</td>
                <td>{fmt(pick(acct, "lignes_mal_formees"))}</td>
                <td className="txt muted">motif brut conservé, non réparées</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div className="panel">
        <h3>
          Fichiers audités
          <span className="hint">plages de dates effectivement observées</span>
        </h3>
        <div className="table-wrap">
          <table className="data">
            <thead>
              <tr>
                <th>Fichier</th>
                <th>Capteur</th>
                <th>Enregistrements</th>
                <th>Analysables</th>
                <th>Hors emprise</th>
                <th>Exclues</th>
                <th>Doublons</th>
                <th>Anomalies</th>
                <th>Période observée</th>
              </tr>
            </thead>
            <tbody>
              {filesPage.pageItems.map((f, i) => (
                <tr key={i}>
                  <td className="txt">{f.file}</td>
                  <td>{f.sensor}</td>
                  <td>{fmt(f.n_records)}</td>
                  <td>{fmt(f.n_rows_analysable)}</td>
                  <td>{fmt(f.n_rows_outside_emprise)}</td>
                  <td>{fmt(f.n_rows_excluded)}</td>
                  <td>{fmt(f.n_duplicate_rows)}</td>
                  <td>{fmt(f.n_anomalies)}</td>
                  <td className="muted">
                    {f.date_min || "—"} → {f.date_max || "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <Pagination
          page={filesPage.page}
          totalPages={filesPage.totalPages}
          total={filesPage.total}
          pageSize={filesPage.pageSize}
          onPageChange={filesPage.setPage}
        />
      </div>

      {a.temporal_gaps?.n_entries > 0 && (
        <div className="panel">
          <h3>
            Trous temporels détectés
            <span className="hint">jours sans enregistrement — jamais « pas de feu »</span>
          </h3>
          <p className="muted small" style={{ marginTop: 0 }}>
            {fmt(a.temporal_gaps.n_entries)} entrée(s) : jours sans enregistrement par capteur,
            sans inference sur l'observabilité (produits de couverture non acquis).
          </p>
          <div className="table-wrap">
            <table className="data">
              <thead>
                <tr>
                  <th>Capteur</th>
                  <th>Date</th>
                  <th>Interprétation</th>
                </tr>
              </thead>
              <tbody>
                {(a.temporal_gaps.entries || []).slice(0, 40).map((g, i) => (
                  <tr key={i}>
                    <td>{g.sensor}</td>
                    <td>{g.date}</td>
                    <td className="txt muted">{g.interpretation}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {(a.temporal_gaps.entries || []).length > 40 && (
            <p className="muted small">
              {a.temporal_gaps.entries.length - 40} entrée(s) supplémentaire(s) dans
              reports/data_quality_audit.md.
            </p>
          )}
        </div>
      )}

      {a.volumes_by_month && Object.keys(a.volumes_by_month).length > 0 && (
        <div className="panel">
          <h3>
            Volumes par mois et capteur
            <span className="hint">comptages de lignes analysables</span>
          </h3>
          <div className="table-wrap">
            <table className="data">
              <thead>
                <tr>
                  <th>Capteur</th>
                  <th>Mois</th>
                  <th>Détections</th>
                </tr>
              </thead>
              <tbody>
                {volPage.pageItems.map((r, i) => (
                  <tr key={i}>
                    <td>{r.sensor}</td>
                    <td>{r.month}</td>
                    <td>{fmt(r.value)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <Pagination
            page={volPage.page}
            totalPages={volPage.totalPages}
            total={volPage.total}
            pageSize={volPage.pageSize}
            onPageChange={volPage.setPage}
          />
        </div>
      )}

      {a.interpretation_warning && (
        <div className="banner warn">
          <strong>Avertissement d'interprétation du pipeline</strong>
          {a.interpretation_warning}
        </div>
      )}

      <div className="panel">
        <h3>
          Distribution de la confiance par capteur
          <span className="hint">échelles distinctes, jamais converties sur un socle commun</span>
        </h3>
        <div className="table-wrap">
          <table className="data">
            <thead>
              <tr>
                <th>Capteur : valeur</th>
                <th>Détections</th>
                <th>Échelle</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(a.confidence_distribution_by_sensor || {})
                .sort((x, y) => y[1] - x[1])
                .map(([k, v], i) => {
                  const [sensor, value] = k.split(":");
                  return (
                    <tr key={i}>
                      <td className="txt">
                        <strong>{sensor}</strong> : {value}
                      </td>
                      <td>{fmt(v)}</td>
                      <td className="txt muted">
                        {sensor === "viirs"
                          ? "catégorielle VIIRS (low/nominal/high) — non mappée"
                          : "numérique MODIS (0–100) — non mappée"}
                      </td>
                    </tr>
                  );
                })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
