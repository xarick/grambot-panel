import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import * as botsApi from "@/api/bots.js";
import { useTranslation } from "@/hooks/useTranslation.jsx";
import { Layout } from "@/components/layout/Layout.jsx";
import { Spinner } from "@/components/ui/Spinner.jsx";

export function ChannelsPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [bots, setBots] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    botsApi
      .list()
      .then(setBots)
      .catch((e) => setError(e.detail || t("common.error")))
      .finally(() => setLoading(false));
  }, [t]);

  return (
    <Layout>
      <div className="p-6 max-w-5xl mx-auto space-y-6">
        <div>
          <h1 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
            {t("chats.title")}
          </h1>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            {t("chats.bots_hint")}
          </p>
        </div>

        {loading ? (
          <div className="flex justify-center py-16"><Spinner size="lg" /></div>
        ) : error ? (
          <p className="text-center py-16 text-sm text-red-500">{error}</p>
        ) : bots.length === 0 ? (
          <p className="text-center py-16 text-gray-500 dark:text-gray-400 text-sm">
            {t("chats.no_bots")}
          </p>
        ) : (
          <div className="space-y-2">
            {bots.map((b) => (
              <button
                key={b.id}
                onClick={() => navigate(`/channels/${b.id}`)}
                className="w-full flex items-center justify-between rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-4 text-left transition-colors hover:bg-gray-50 dark:hover:bg-gray-700/40"
              >
                <div className="flex items-center gap-3 min-w-0">
                  <div className="w-9 h-9 shrink-0 rounded-full bg-blue-100 dark:bg-blue-900/40 flex items-center justify-center text-blue-600 dark:text-blue-400 text-sm font-semibold">
                    {b.name[0]?.toUpperCase()}
                  </div>
                  <div className="min-w-0">
                    <div className="font-medium text-gray-900 dark:text-gray-100 truncate">
                      {b.name}
                    </div>
                    {b.username && (
                      <div className="text-xs text-gray-500 dark:text-gray-400 truncate">
                        @{b.username}
                      </div>
                    )}
                  </div>
                </div>
                <svg className="w-5 h-5 shrink-0 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </button>
            ))}
          </div>
        )}
      </div>
    </Layout>
  );
}
