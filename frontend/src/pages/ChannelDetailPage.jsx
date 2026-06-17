import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import * as botsApi from "@/api/bots.js";
import { useTranslation } from "@/hooks/useTranslation.jsx";
import { Layout } from "@/components/layout/Layout.jsx";
import { Button } from "@/components/ui/Button.jsx";
import { Badge } from "@/components/ui/Badge.jsx";
import { Spinner } from "@/components/ui/Spinner.jsx";
import { formatDateTime } from "@/utils/format.js";

export function ChannelDetailPage() {
  const { botId, chatRowId } = useParams();
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [info, setInfo] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    setLoading(true);
    botsApi
      .chatInfo(botId, chatRowId)
      .then(setInfo)
      .catch((e) => setError(e.detail || t("common.error")))
      .finally(() => setLoading(false));
  }, [botId, chatRowId, t]);

  const refresh = async () => {
    setRefreshing(true);
    setError("");
    try {
      setInfo(await botsApi.refreshChat(botId, chatRowId));
    } catch (e) {
      setError(e.detail || t("common.error"));
    } finally {
      setRefreshing(false);
    }
  };

  const admins = info?.admins || [];

  return (
    <Layout>
      <div className="p-6 max-w-5xl mx-auto space-y-6">
        <div className="flex items-start justify-between gap-4">
          <div className="min-w-0">
            <button
              onClick={() => navigate(`/channels/${botId}`)}
              className="text-sm text-gray-500 hover:text-blue-500 dark:text-gray-400 mb-2 inline-flex items-center gap-1"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
              {t("chats.back")}
            </button>
            <h1 className="text-xl font-semibold text-gray-900 dark:text-gray-100 truncate">
              {info?.title || "—"}
            </h1>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
              {info?.synced_at
                ? `${t("chats.synced_at")}: ${formatDateTime(info.synced_at)}`
                : t("chats.never_synced")}
            </p>
          </div>
          <Button size="sm" onClick={refresh} disabled={refreshing || loading}>
            {refreshing ? t("chats.refreshing") : t("chats.refresh")}
          </Button>
        </div>

        {loading ? (
          <div className="flex justify-center py-16"><Spinner size="lg" /></div>
        ) : error ? (
          <p className="text-center py-10 text-sm text-red-500">{error}</p>
        ) : info ? (
          <div className="space-y-5">
            <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5">
              <dl className="text-sm divide-y divide-gray-100 dark:divide-gray-700">
                {[
                  [t("chats.f_type"), info.type ? t(`chats.type_${info.type}`) : "—"],
                  [t("chats.f_username"), info.username ? `@${info.username}` : "—"],
                  [t("chats.f_members"), info.member_count ?? "—"],
                  [t("chats.f_bot_status"), info.bot_status || "—"],
                  [t("chats.f_id"), info.chat_id],
                ].map(([k, v]) => (
                  <div key={k} className="flex justify-between py-2">
                    <dt className="text-gray-500 dark:text-gray-400">{k}</dt>
                    <dd className="font-medium text-gray-900 dark:text-gray-100">{v}</dd>
                  </div>
                ))}
              </dl>
              {info.description && (
                <p className="mt-3 text-sm text-gray-600 dark:text-gray-400 whitespace-pre-wrap">
                  {info.description}
                </p>
              )}
            </div>

            <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5">
              <div className="text-xs font-medium uppercase tracking-wide text-gray-500 dark:text-gray-400 mb-2">
                {t("chats.admins")} ({admins.length})
              </div>
              {admins.length === 0 ? (
                <p className="text-sm text-gray-500 dark:text-gray-400">—</p>
              ) : (
                <div className="space-y-1.5 text-sm">
                  {admins.map((a) => (
                    <div key={a.id} className="flex items-center justify-between">
                      <span className="text-gray-800 dark:text-gray-200 truncate">
                        {a.name}
                        {a.username && <span className="text-gray-400"> @{a.username}</span>}
                        {a.is_bot && <span className="ml-1 text-xs text-gray-400">[bot]</span>}
                      </span>
                      <Badge color={a.status === "creator" ? "purple" : "gray"}>
                        {a.status}
                      </Badge>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {!info.synced_at && (
              <p className="text-center text-sm text-gray-500 dark:text-gray-400">
                {t("chats.never_synced")}
              </p>
            )}
          </div>
        ) : null}
      </div>
    </Layout>
  );
}
