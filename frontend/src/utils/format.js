const pad = (n) => String(n).padStart(2, "0");

/**
 * Format a timestamp the way it looks in the database: `YYYY-MM-DD HH:MM`.
 * No slashes, no AM/PM — day, month, year and 24h time. Local timezone.
 */
export function formatDateTime(value) {
  if (!value) return "—";
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return "—";
  return (
    `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ` +
    `${pad(d.getHours())}:${pad(d.getMinutes())}`
  );
}
