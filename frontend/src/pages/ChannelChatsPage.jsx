import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import * as botsApi from "@/api/bots.js";
import { useTranslation } from "@/hooks/useTranslation.jsx";
import { Layout } from "@/components/layout/Layout.jsx";
import { Badge } from "@/components/ui/Badge.jsx";
import { Spinner } from "@/components/ui/Spinner.jsx";
import { formatDateTime } from "@/utils/format.js";

const TYPE_COLOR = { channel: "purple", supergroup: "blue", group: "blue" };

export function ChannelChatsPage() {
  const { botId } = useParams();
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [bot, setBot] = useState(null);
  const [chats, setChats] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    setLoading(true);
    Promise.all([botsApi.list(), botsApi.listChats(botId)])
      .then(([bots, chatList]) => {
        setBot(bots.find((b) => String(b.id) === String(botId)) || null);
        setChats(chatList);
      })
      .catch((e) => setError(e.detail || t("common.error")))
      .finally(() => setLoading(false));
  }, [botId, t]);

  return (
    <Layout>
      <div className="p-6 max-w-5xl mx-auto space-y-6">
        <div>
          <button
            onClick={() => navigate("/channels")}
            className="text-sm text-gray-500 hover:text-blue-500 dark:text-gray-400 mb-2 inline-flex items-center gap-1"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            {t("chats.back")}
          </button>
          <h1 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
            {t("chats.title")}
            {bot && <span className="text-gray-400 font-normal"> — {bot.name}</span>}
          </h1>
        </div>

        {loading ? (
          <div className="flex justify-center py-16"><Spinner size="lg" /></div>
        ) : error ? (
          <p className="text-center py-16 text-sm text-red-500">{error}</p>
        ) : chats.length === 0 ? (
          <p className="text-center py-16 text-gray-500 dark:text-gray-400 text-sm">
            {t("chats.empty")}
          </p>
        ) : (
          <div className="space-y-2">
            {chats.map((c) => (
              <button
                key={c.id}
                onClick={() => navigate(`/channels/${botId}/${c.id}`)}
                className="w-full flex items-center justify-between rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-4 text-left transition-colors hover:bg-gray-50 dark:hover:bg-gray-700/40"
              >
                <div className="min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="font-medium text-gray-900 dark:text-gray-100 truncate">
                      {c.title || c.chat_id}
                    </span>
                    <Badge color={TYPE_COLOR[c.type] || "gray"}>
                      {t(`chats.type_${c.type}`)}
                    </Badge>
                  </div>
                  <div className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                    {c.username ? `@${c.username} · ` : ""}
                    {c.synced_at
                      ? `${t("chats.synced_at")}: ${formatDateTime(c.synced_at)}`
                      : t("chats.never_synced")}
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
