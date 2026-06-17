import { useEffect, useState } from "react";
import * as statsApi from "@/api/stats.js";
import { useTranslation } from "@/hooks/useTranslation.jsx";
import { Spinner } from "@/components/ui/Spinner.jsx";

const DAYS = 14;

function Kpi({ label, value }) {
  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4">
      <div className="text-2xl font-bold text-gray-900 dark:text-gray-100">{value}</div>
      <div className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">{label}</div>
    </div>
  );
}

function BarChart({ title, points, accessor, color }) {
  const max = Math.max(1, ...points.map(accessor));
  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4">
      <div className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">{title}</div>
      <div className="flex items-end gap-1 h-28">
        {points.map((p) => {
          const v = accessor(p);
          return (
            <div
              key={p.date}
              className="flex-1 flex flex-col justify-end"
              title={`${p.date}: ${v}`}
            >
              <div
                className={`${color} rounded-t transition-all`}
                style={{ height: `${(v / max) * 100}%`, minHeight: v > 0 ? "3px" : "0" }}
              />
            </div>
          );
        })}
      </div>
      <div className="flex justify-between text-[10px] text-gray-400 mt-1">
        <span>{points[0]?.date.slice(5)}</span>
        <span>{points[points.length - 1]?.date.slice(5)}</span>
      </div>
    </div>
  );
}

export function StatsPanel() {
  const { t } = useTranslation();
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    statsApi
      .get(DAYS)
      .then(setStats)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex justify-center py-10">
        <Spinner />
      </div>
    );
  }
  if (!stats) return null;

  const { totals, series, top_bots } = stats;
  const maxBotMsgs = Math.max(1, ...top_bots.map((b) => b.messages));

  return (
    <div className="mb-8 space-y-4">
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <Kpi label={t("stats.subscribers")} value={totals.subscribers} />
        <Kpi label={t("stats.new_subs", { days: DAYS })} value={totals.new_subscribers_period} />
        <Kpi label={t("stats.messages")} value={totals.messages} />
        <Kpi label={t("stats.bots")} value={totals.bots} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
        <BarChart
          title={t("stats.new_subscribers")}
          points={series}
          accessor={(p) => p.new_subscribers}
          color="bg-blue-500"
        />
        <BarChart
          title={t("stats.messages_in")}
          points={series}
          accessor={(p) => p.messages_in + p.messages_out}
          color="bg-emerald-500"
        />
      </div>

      <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4">
        <div className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">{t("stats.top_bots")}</div>
        {top_bots.length === 0 ? (
          <p className="text-sm text-gray-500 dark:text-gray-400">{t("stats.no_data")}</p>
        ) : (
          <div className="space-y-2">
            {top_bots.map((b) => (
              <div key={b.bot_id} className="flex items-center gap-3">
                <span className="w-32 truncate text-sm text-gray-700 dark:text-gray-300">{b.name}</span>
                <div className="flex-1 h-2 bg-gray-100 dark:bg-gray-700 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-blue-500 rounded-full"
                    style={{ width: `${(b.messages / maxBotMsgs) * 100}%` }}
                  />
                </div>
                <span className="w-12 text-right text-sm tabular-nums text-gray-500 dark:text-gray-400">
                  {b.messages}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
