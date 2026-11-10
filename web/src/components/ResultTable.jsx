/**
 * ResultTable - Component for displaying result data in table format
 * Used by: ExperimentDetail
 * 
 * @param {Array} columns - Column definitions [{key, label}]
 * @param {Array} data - Row data
 * @param {function} formatCell - Optional cell formatter
 */
export default function ResultTable({ columns, data, formatCell }) {
  if (!data || data.length === 0) {
    return (
      <div style={{ textAlign: "center", padding: "20px" }}>
        <p className="muted">Aucune donnée disponible</p>
      </div>
    );
  }

  return (
    <div className="table-wrap">
      <table className="data">
        <thead>
          <tr>
            {columns.map((col) => (
              <th key={col.key}>{col.label}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.map((row, i) => (
            <tr key={i}>
              {columns.map((col) => (
                <td key={col.key} className={col.className || ""}>
                  {formatCell ? formatCell(col.key, row[col.key]) : row[col.key]}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
