import { useCallback, useEffect, useRef, useState } from "react";
import { useParams } from "react-router-dom";
import * as convApi from "@/api/conversations.js";
import * as templatesApi from "@/api/templates.js";
import { useTranslation } from "@/hooks/useTranslation.jsx";
import { usePolling } from "@/hooks/usePolling.js";
import { Layout } from "@/components/layout/Layout.jsx";
import { Button } from "@/components/ui/Button.jsx";
import { Badge } from "@/components/ui/Badge.jsx";
import { Spinner } from "@/components/ui/Spinner.jsx";

function formatTime(dateStr) {
  if (!dateStr) return "";
  const d = new Date(dateStr);
  return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function formatDate(dateStr) {
  if (!dateStr) return "";
  const d = new Date(dateStr);
  return d.toLocaleDateString([], { month: "short", day: "numeric" });
}

export function InboxPage() {
  const { botId } = useParams();
  const { t } = useTranslation();

  const [conversations, setConversations] = useState([]);
  const [total, setTotal] = useState(0);
  const [search, setSearch] = useState("");
  const [tag, setTag] = useState("");
  const [selectedId, setSelectedId] = useState(null);
  const [loadingList, setLoadingList] = useState(true);
  const [offset, setOffset] = useState(0);
  const LIMIT = 50;

  const loadConversations = useCallback(async () => {
    const data = await convApi.listByBot(botId, { search, tag: tag || undefined, limit: LIMIT, offset });
    setConversations(data.items);
    setTotal(data.total);
    setLoadingList(false);
  }, [botId, search, tag, offset]);

  useEffect(() => { setLoadingList(true); loadConversations(); }, [loadConversations]);
  usePolling(loadConversations, 5000);

  return (
    <Layout>
      <div className="flex h-full">
        <aside className="w-80 shrink-0 flex flex-col border-r border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900">
          <div className="p-4 border-b border-gray-200 dark:border-gray-700">
            <div className="relative">
              <svg className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
              <input
                className="w-full pl-9 pr-4 py-2 text-sm rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder={t("inbox.search")}
                value={search}
                onChange={(e) => { setSearch(e.target.value); setOffset(0); }}
              />
            </div>
            <input
              className="mt-2 w-full px-3 py-2 text-sm rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder={t("inbox.filter_tag")}
              value={tag}
              onChange={(e) => { setTag(e.target.value); setOffset(0); }}
            />
          </div>

          <div className="flex-1 overflow-y-auto">
            {loadingList ? (
              <div className="flex justify-center py-10"><Spinner /></div>
            ) : conversations.length === 0 ? (
              <p className="text-center text-gray-500 dark:text-gray-400 py-10 text-sm">{t("inbox.no_conversations")}</p>
            ) : (
              conversations.map((conv) => (
                <button
                  key={conv.id}
                  onClick={() => setSelectedId(conv.id)}
                  className={`w-full text-left px-4 py-3 border-b border-gray-100 dark:border-gray-800 transition-colors ${
                    selectedId === conv.id
                      ? "bg-blue-50 dark:bg-blue-900/20"
                      : "hover:bg-gray-50 dark:hover:bg-gray-800"
                  }`}
                >
                  <div className="flex items-center justify-between mb-0.5">
                    <span className="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">
                      {conv.user.full_name}
                    </span>
                    <span className="text-xs text-gray-400 shrink-0 ml-2">{formatDate(conv.last_message_at)}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    {conv.user.username && (
                      <span className="text-xs text-gray-500 dark:text-gray-400">@{conv.user.username}</span>
                    )}
                    {conv.unread_count > 0 && (
                      <span className="ml-auto inline-flex items-center justify-center w-5 h-5 text-xs font-bold bg-blue-600 text-white rounded-full">
                        {conv.unread_count > 9 ? "9+" : conv.unread_count}
                      </span>
                    )}
                    {!conv.is_open && <Badge color="gray">{t("inbox.closed")}</Badge>}
                    {conv.user.is_blocked && <Badge color="red">{t("inbox.blocked")}</Badge>}
                  </div>
                </button>
              ))
            )}
          </div>

          {total > LIMIT && (
            <div className="p-3 border-t border-gray-200 dark:border-gray-700 flex gap-2">
              <Button size="sm" variant="secondary" disabled={offset === 0} onClick={() => setOffset((o) => Math.max(0, o - LIMIT))}>
                ←
              </Button>
              <Button size="sm" variant="secondary" disabled={offset + LIMIT >= total} onClick={() => setOffset((o) => o + LIMIT)}>
                →
              </Button>
            </div>
          )}
        </aside>

        <div className="flex-1 flex flex-col">
          {selectedId ? (
            <ChatPanel key={selectedId} convId={selectedId} t={t} />
          ) : (
            <div className="flex-1 flex items-center justify-center text-gray-500 dark:text-gray-400 text-sm">
              {t("inbox.select_conversation")}
            </div>
          )}
        </div>
      </div>
    </Layout>
  );
}

function ChatPanel({ convId, t }) {
  const [conv, setConv] = useState(null);
  const [messages, setMessages] = useState([]);
  const [hasMore, setHasMore] = useState(false);
  const [text, setText] = useState("");
  const [sending, setSending] = useState(false);
  const [templates, setTemplates] = useState([]);
  const [showTemplates, setShowTemplates] = useState(false);
  const bottomRef = useRef(null);
  const lastIdRef = useRef(0);

  useEffect(() => {
    convApi.get(convId).then(setConv);
    templatesApi.list().then(setTemplates);
    convApi.getMessages(convId).then((data) => {
      setMessages(data.items || []);
      setHasMore(data.has_more || false);
      if (data.items?.length) lastIdRef.current = data.items[data.items.length - 1].id;
    });
  }, [convId]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const poll = useCallback(async () => {
    if (!lastIdRef.current) return;
    const newMsgs = await convApi.getMessages(convId, lastIdRef.current);
    if (Array.isArray(newMsgs) && newMsgs.length > 0) {
      setMessages((prev) => [...prev, ...newMsgs]);
      lastIdRef.current = newMsgs[newMsgs.length - 1].id;
    }
  }, [convId]);

  usePolling(poll, 3000, !!conv);

  const loadMore = async () => {
    if (!messages.length) return;
    const older = await convApi.getMessages(convId, 0, messages[0].id);
    if (Array.isArray(older) && older.length > 0) {
      setMessages((prev) => [...older, ...prev]);
      if (older.length < 50) setHasMore(false);
    }
  };

  const sendMessage = async () => {
    if (!text.trim()) return;
    setSending(true);
    try {
      const msg = await convApi.reply(convId, text.trim());
      setMessages((prev) => [...prev, msg]);
      lastIdRef.current = msg.id;
      setText("");
    } catch (err) {
      alert(err.detail);
    } finally {
      setSending(false);
    }
  };

  const toggleBlock = async () => {
    if (!conv) return;
    await convApi.blockUser(convId, !conv.user.is_blocked);
    const updated = await convApi.get(convId);
    setConv(updated);
  };

  const toggleOpen = async () => {
    if (!conv) return;
    await convApi.update(convId, { is_open: !conv.is_open });
    const updated = await convApi.get(convId);
    setConv(updated);
  };

  if (!conv) return <div className="flex-1 flex items-center justify-center"><Spinner size="lg" /></div>;

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900">
        <div>
          <div className="font-semibold text-gray-900 dark:text-gray-100">{conv.user.full_name}</div>
          {conv.user.username && (
            <div className="text-xs text-gray-500">@{conv.user.username}</div>
          )}
        </div>
        <div className="flex items-center gap-2">
          {conv.user.is_blocked && <Badge color="red">{t("inbox.blocked")}</Badge>}
          {!conv.is_open && <Badge color="gray">{t("inbox.closed")}</Badge>}
          <Button size="sm" variant="ghost" onClick={toggleBlock}>
            {conv.user.is_blocked ? t("inbox.unblock") : t("inbox.block")}
          </Button>
          <Button size="sm" variant="secondary" onClick={toggleOpen}>
            {conv.is_open ? t("inbox.close") : t("inbox.reopen")}
          </Button>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-3 bg-gray-50 dark:bg-gray-950">
        {hasMore && (
          <div className="text-center">
            <Button size="sm" variant="ghost" onClick={loadMore}>{t("inbox.load_more")}</Button>
          </div>
        )}
        {messages.map((msg) => (
          <MessageBubble key={msg.id} msg={msg} />
        ))}
        <div ref={bottomRef} />
      </div>

      <div className="px-4 py-3 border-t border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900">
        {showTemplates && templates.length > 0 && (
          <div className="mb-2 p-2 bg-gray-50 dark:bg-gray-800 rounded-lg max-h-40 overflow-y-auto space-y-1">
            {templates.map((tpl) => (
              <button
                key={tpl.id}
                onClick={() => { setText(tpl.text); setShowTemplates(false); }}
                className="w-full text-left px-3 py-1.5 rounded text-sm hover:bg-white dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300 transition-colors"
              >
                <span className="font-medium">{tpl.title}</span>
                <span className="text-gray-400 ml-2 text-xs truncate">{tpl.text}</span>
              </button>
            ))}
          </div>
        )}
        <div className="flex gap-2">
          <Button size="sm" variant="ghost" onClick={() => setShowTemplates((s) => !s)} title={t("inbox.templates")}>
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </Button>
          <input
            className="flex-1 px-3 py-2 text-sm rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder={t("inbox.type_message")}
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && sendMessage()}
          />
          <Button size="sm" onClick={sendMessage} disabled={sending || !text.trim()}>
            {t("inbox.send")}
          </Button>
        </div>
      </div>
    </div>
  );
}

function MessageBubble({ msg }) {
  const isOut = msg.direction === "outgoing";
  return (
    <div className={`flex ${isOut ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-xs lg:max-w-md px-3 py-2 rounded-2xl text-sm ${
          isOut
            ? "bg-blue-600 text-white rounded-br-sm"
            : "bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 border border-gray-200 dark:border-gray-700 rounded-bl-sm"
        }`}
      >
        {msg.message_type === "photo" && msg.file_id && (
          <a href={`/api/v1/messages/${msg.id}/file`} target="_blank" rel="noopener noreferrer">
            <div className="mb-1 text-xs opacity-70">[Photo]</div>
          </a>
        )}
        {msg.message_type === "document" && msg.file_id && (
          <a
            href={`/api/v1/messages/${msg.id}/file`}
            target="_blank"
            rel="noopener noreferrer"
            className={`text-xs underline block mb-1 ${isOut ? "text-blue-200" : "text-blue-600"}`}
          >
            {msg.file_name || "Document"}
          </a>
        )}
        {msg.message_type === "sticker" && <div className="text-xs opacity-70 mb-1">[Sticker]</div>}
        {msg.text && <p className="whitespace-pre-wrap break-words">{msg.text}</p>}
        <div className={`text-xs mt-1 ${isOut ? "text-blue-200" : "text-gray-400"} text-right`}>
          {formatTime(msg.sent_at)}
        </div>
      </div>
    </div>
  );
}
