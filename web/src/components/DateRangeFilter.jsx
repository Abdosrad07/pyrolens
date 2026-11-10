/**
 * DateRangeFilter - Component for selecting date ranges
 * Used by: Overview, Fire Calendar, Harmonization Lab, Data Catalog
 * 
 * @param {string} startDate - Start date in ISO format (YYYY-MM-DD)
 * @param {string} endDate - End date in ISO format (YYYY-MM-DD)
 * @param {function} onStartDateChange - Callback when start date changes
 * @param {function} onEndDateChange - Callback when end date changes
 * @param {string} minDate - Optional minimum date
 * @param {string} maxDate - Optional maximum date
 */
export default function DateRangeFilter({
  startDate,
  endDate,
  onStartDateChange,
  onEndDateChange,
  minDate,
  maxDate,
}) {
  return (
    <div className="controls">
      <label htmlFor="start-date">Date de début</label>
      <input
        id="start-date"
        type="date"
        value={startDate}
        min={minDate}
        max={maxDate}
        onChange={(e) => onStartDateChange(e.target.value)}
        className="mono"
      />
      <label htmlFor="end-date" style={{ marginLeft: "12px" }}>
        Date de fin
      </label>
      <input
        id="end-date"
        type="date"
        value={endDate}
        min={minDate}
        max={maxDate}
        onChange={(e) => onEndDateChange(e.target.value)}
        className="mono"
      />
    </div>
  );
}
