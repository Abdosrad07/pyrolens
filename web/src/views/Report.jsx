import { Fragment, useMemo } from "react";

/** Mini-rendu Markdown (titres, listes, tableaux, gras, code) — sans dépendance. */
function renderMarkdown(md) {
  const lines = md.split("\n");
  const blocks = [];
  let i = 0;

  const inline = (text, key) => {
    const parts = text.split(/(\*\*[^*]+\*\*|`[^`]+`)/g).filter(Boolean);
    return (
      <Fragment key={key}>
        {parts.map((p, k) => {
          if (p.startsWith("**") && p.endsWith("**"))
            return <strong key={k}>{p.slice(2, -2)}</strong>;
          if (p.startsWith("`") && p.endsWith("`"))
            return <code key={k}>{p.slice(1, -1)}</code>;
          return <Fragment key={k}>{p}</Fragment>;
        })}
      </Fragment>
    );
  };

  while (i < lines.length) {
    const line = lines[i];

    if (line.startsWith("|")) {
      const rows = [];
      while (i < lines.length && lines[i].startsWith("|")) {
        rows.push(lines[i]);
        i++;
      }
      const cells = (r) =>
        r
          .replace(/^\||\|$/g, "")
          .split("|")
          .map((c) => c.trim());
      const header = cells(rows[0]);
      const body = rows
        .slice(2)
        .filter((r) => !/^\|[\s:|-]+\|$/.test(r))
        .map(cells);
      blocks.push(
        <table key={`t${i}`}>
          <thead>
            <tr>
              {header.map((h, k) => (
                <th key={k}>{inline(h, k)}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {body.map((r, ri) => (
              <tr key={ri}>
                {r.map((c, k) => (
                  <td key={k}>{inline(c, k)}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      );
      continue;
    }

    if (line.startsWith("### ")) {
      blocks.push(<h3 key={i}>{inline(line.slice(4), i)}</h3>);
    } else if (line.startsWith("## ")) {
      blocks.push(<h2 key={i}>{inline(line.slice(3), i)}</h2>);
    } else if (line.startsWith("# ")) {
      blocks.push(<h1 key={i}>{inline(line.slice(2), i)}</h1>);
    } else if (/^[-*] /.test(line)) {
      const items = [];
      while (i < lines.length && /^[-*] /.test(lines[i])) {
        items.push(lines[i].slice(2));
        i++;
      }
      blocks.push(
        <ul key={`u${i}`}>
          {items.map((it, k) => (
            <li key={k}>{inline(it, k)}</li>
          ))}
        </ul>
      );
      continue;
    } else if (line.startsWith("```")) {
      const buf = [];
      i++;
      while (i < lines.length && !lines[i].startsWith("```")) {
        buf.push(lines[i]);
        i++;
      }
      blocks.push(<pre key={`p${i}`}>{buf.join("\n")}</pre>);
    } else if (line.trim() !== "") {
      blocks.push(<p key={i}>{inline(line, i)}</p>);
    }
    i++;
  }
  return blocks;
}

export default function Report({ data }) {
  const md = data.report;
  const rendered = useMemo(() => (md ? renderMarkdown(md) : null), [md]);

  if (!md)
    return (
      <div className="loading">
        Rapport scientific_report.json/md indisponible — exécutez <span className="mono">pyrolens report</span>.
      </div>
    );

  const origin = data.audit?.data_origin;

  return (
    <div>
      <h2 className="page-title">Rapport scientifique</h2>
      <p className="page-sub">
        Généré par le pipeline : <span className="mono">reports/scientific_report.md</span> (+
        DOCX). Chaque chiffre y est soit calculé par le pipeline, soit explicitement étiqueté
        comme valeur de référence antérieure.
      </p>
      {origin === "synthetic_fixture" && (
        <div className="banner warn">
          <strong>Origine des données : échantillon synthétique de démonstration</strong>
          Les métriques ci-dessous portent cette étiquette dans le rapport lui-même.
        </div>
      )}
      <div className="panel">
        <div className="md">{rendered}</div>
      </div>
    </div>
  );
}
