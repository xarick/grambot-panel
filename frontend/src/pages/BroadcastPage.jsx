import { useCallback, useEffect, useState } from "react";
import * as broadcastApi from "@/api/broadcast.js";
import * as botsApi from "@/api/bots.js";
import { useTranslation } from "@/hooks/useTranslation.jsx";
import { usePolling } from "@/hooks/usePolling.js";
import { Layout } from "@/components/layout/Layout.jsx";
import { Button } from "@/components/ui/Button.jsx";
import { Input, Textarea, Select } from "@/components/ui/Input.jsx";
import { Badge } from "@/components/ui/Badge.jsx";
import { Spinner } from "@/components/ui/Spinner.jsx";
import { Modal } from "@/components/ui/Modal.jsx";
import { formatDateTime } from "@/utils/format.js";

const STATUS_COLORS = {
  draft: "gray",
  scheduled: "purple",
  sending: "blue",
  sent: "green",
  failed: "red",
  canceled: "gray",
};

const PAGE_SIZE_OPTIONS = [10, 20, 50];
const TEXT_LIMIT = 4096;
const CAPTION_LIMIT = 1024;
const MAX_BUTTONS = 8;
const TERMINAL_STATUSES = new Set(["sent", "failed", "canceled"]);
const ACTIVE_STATUSES = new Set(["sending", "draft", "scheduled"]);

function getPageRange(current, total) {
  if (total <= 7) {
    return Array.from({ length: total }, (_, i) => i + 1);
  }
  const pages = [1];
  const start = Math.max(2, current - 1);
  const end = Math.min(total - 1, current + 1);
  if (start > 2) pages.push("…");
  for (let i = start; i <= end; i++) pages.push(i);
  if (end < total - 1) pages.push("…");
  pages.push(total);
  return pages;
}

// datetime-local expects "YYYY-MM-DDTHH:MM" in LOCAL time (no tz), so we
// format the current moment in the user's tz to use as the `min` attribute.
function localDatetimeNow() {
  const now = new Date();
  const pad = (n) => String(n).padStart(2, "0");
  return `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}T${pad(now.getHours())}:${pad(now.getMinutes())}`;
}

export function BroadcastPage() {
  const { t } = useTranslation();
  const [bots, setBots] = useState([]);
  const [history, setHistory] = useState([]);
  const [historyTotal, setHistoryTotal] = useState(0);
  const [historyOffset, setHistoryOffset] = useState(0);
  const [historyLimit, setHistoryLimit] = useState(20);
  const [loading, setLoading] = useState(true);
  const [form, setForm] = useState({
    bot_id: "",
    text: "",
    scheduled_at: "",
    media_type: "",
    media_path: "",
    media_name: "",
    buttons: [],
  });
  const [sending, setSending] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");
  const [activeId, setActiveId] = useState(null);
  const [confirm, setConfirm] = useState(null); // { count, botName }
  // Single shared modal for cancel/delete row actions. Pattern is centralized
  // so styling stays consistent and we don't render a Modal per row.
  const [actionModal, setActionModal] = useState(null);
  // { kind: "cancel"|"delete", broadcast, loading: bool, error: str }

  const loadHistory = useCallback(async () => {
    const data = await broadcastApi.list({ limit: historyLimit, offset: historyOffset });
    // After a delete drains the last row off a non-first page, the current
    // offset lands past `total`. Slide back to the last valid page so the
    // user doesn't stare at an empty list with hidden pagination.
    if (data.total > 0 && historyOffset >= data.total) {
      const lastPageOffset = (Math.ceil(data.total / historyLimit) - 1) * historyLimit;
      setHistoryOffset(lastPageOffset);
      return;
    }
    setHistory(data.items);
    setHistoryTotal(data.total);
    setLoading(false);
    // Poll while any visible broadcast is still pending — scheduled rows
    // need refreshes too so their status flips when the worker fires.
    const active = data.items.find((b) => ACTIVE_STATUSES.has(b.status));
    setActiveId(active ? active.id : null);
  }, [historyLimit, historyOffset]);

  useEffect(() => {
    botsApi.list().then(setBots);
  }, []);

  useEffect(() => {
    loadHistory();
  }, [loadHistory]);

  usePolling(loadHistory, 2000, !!activeId);

  const textLimit = form.media_path ? CAPTION_LIMIT : TEXT_LIMIT;
  const textLength = form.text.length;
  const overLimit = textLength > textLimit;

  const canSend =
    form.bot_id && (form.text.trim() || form.media_path) && !overLimit;

  const handleUpload = async (file) => {
    if (!file) return;
    setUploading(true);
    setError("");
    try {
      const res = await broadcastApi.uploadMedia(file);
      setForm((f) => ({ ...f, media_type: res.media_type, media_path: res.media_path, media_name: file.name }));
    } catch (err) {
      setError(err.detail || t("common.error"));
    } finally {
      setUploading(false);
    }
  };

  const requestSend = async () => {
    if (!canSend) return;
    setError("");
    try {
      const { count } = await broadcastApi.recipients(parseInt(form.bot_id));
      const botName = bots.find((b) => b.id === parseInt(form.bot_id))?.name || "";
      if (count === 0) {
        setError(t("broadcast.no_recipients"));
        return;
      }
      setConfirm({ count, botName });
    } catch (err) {
      setError(err.detail || t("common.error"));
    }
  };

  const runAction = async () => {
    if (!actionModal) return;
    setActionModal((m) => ({ ...m, loading: true, error: "" }));
    try {
      if (actionModal.kind === "cancel") {
        await broadcastApi.cancel(actionModal.broadcast.id);
      } else if (actionModal.kind === "delete") {
        await broadcastApi.remove(actionModal.broadcast.id);
      }
      setActionModal(null);
      await loadHistory();
    } catch (err) {
      setActionModal((m) => (m ? { ...m, loading: false, error: err.detail || t("common.error") } : null));
    }
  };

  const confirmSend = async () => {
    setSending(true);
    setError("");
    try {
      await broadcastApi.create({
        bot_id: parseInt(form.bot_id),
        text: form.text,
        scheduled_at: form.scheduled_at ? new Date(form.scheduled_at).toISOString() : null,
        media_type: form.media_type,
        media_path: form.media_path,
        buttons: form.buttons.filter((b) => b.text && b.url),
      });
      setForm((f) => ({
        ...f, text: "", scheduled_at: "",
        media_type: "", media_path: "", media_name: "", buttons: [],
      }));
      setConfirm(null);
      if (historyOffset !== 0) {
        setHistoryOffset(0);
      } else {
        await loadHistory();
      }
    } catch (err) {
      setError(err.detail || t("common.error"));
    } finally {
      setSending(false);
    }
  };

  return (
    <Layout>
      <div className="h-full flex flex-col lg:flex-row gap-6 p-6 overflow-hidden">
        {/* Left: compose */}
        <div className="lg:w-[420px] lg:shrink-0 flex flex-col gap-4 lg:overflow-y-auto lg:min-h-0 lg:pr-1">
          <h1 className="text-xl font-semibold text-gray-900 dark:text-gray-100">{t("broadcast.title")}</h1>
          <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5 space-y-4">
            <h2 className="font-medium text-gray-900 dark:text-gray-100">{t("broadcast.compose")}</h2>
            <Select
              label={t("broadcast.select_bot")}
              value={form.bot_id}
              onChange={(e) => setForm((f) => ({ ...f, bot_id: e.target.value }))}
            >
              <option value="" disabled>{t("broadcast.choose_bot")}</option>
              {bots.map((bot) => (
                <option key={bot.id} value={bot.id}>{bot.name} (@{bot.username})</option>
              ))}
            </Select>
            <div>
              <Textarea
                label={t("broadcast.message_text")}
                rows={4}
                value={form.text}
                onChange={(e) => setForm((f) => ({ ...f, text: e.target.value }))}
                placeholder={t("broadcast.message_text")}
                maxLength={TEXT_LIMIT}
              />
              <div className="flex justify-end items-center gap-1.5 mt-1">
                {form.media_path && (
                  <span className="text-xs text-gray-400 dark:text-gray-500">
                    {t("broadcast.text_count_caption_hint")}
                  </span>
                )}
                <span className={`text-xs tabular-nums ${overLimit ? "text-red-500 font-medium" : textLength > textLimit * 0.9 ? "text-amber-500" : "text-gray-400 dark:text-gray-500"}`}>
                  {t("broadcast.text_count", { count: textLength, limit: textLimit })}
                </span>
              </div>
            </div>

            <Input
              label={t("broadcast.schedule")}
              type="datetime-local"
              min={localDatetimeNow()}
              value={form.scheduled_at}
              onChange={(e) => setForm((f) => ({ ...f, scheduled_at: e.target.value }))}
            />

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                {t("broadcast.media")}
              </label>
              {form.media_path ? (
                <div className="flex items-center gap-2 text-sm">
                  <span className="truncate text-gray-600 dark:text-gray-300">
                    {form.media_name} ({form.media_type})
                  </span>
                  <button
                    type="button"
                    className="text-red-500 hover:underline"
                    onClick={() => setForm((f) => ({ ...f, media_type: "", media_path: "", media_name: "" }))}
                  >
                    {t("broadcast.media_remove")}
                  </button>
                </div>
              ) : (
                <input
                  type="file"
                  disabled={uploading}
                  onChange={(e) => handleUpload(e.target.files?.[0])}
                  className="block w-full text-sm text-gray-500 file:mr-3 file:rounded-lg file:border-0 file:bg-blue-50 file:px-3 file:py-1.5 file:text-blue-700 dark:file:bg-blue-900/30 dark:file:text-blue-300"
                />
              )}
              {uploading && <p className="text-xs text-gray-400 mt-1">{t("broadcast.uploading")}</p>}
            </div>

            <div>
              <div className="flex items-center justify-between mb-1">
                <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  {t("broadcast.buttons")}
                </label>
                <button
                  type="button"
                  className="text-xs text-blue-600 hover:underline disabled:text-gray-400 disabled:no-underline disabled:cursor-not-allowed"
                  disabled={form.buttons.length >= MAX_BUTTONS}
                  onClick={() => setForm((f) => ({ ...f, buttons: [...f.buttons, { text: "", url: "" }] }))}
                >
                  + {t("broadcast.add_button")}
                </button>
              </div>
              {form.buttons.map((b, idx) => (
                <div key={idx} className="mb-3 space-y-1.5">
                  <div className="flex gap-2">
                    <input
                      className="flex-1 min-w-0 px-2 py-1.5 text-sm rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800 text-gray-900 dark:text-gray-100"
                      placeholder={t("broadcast.btn_text")}
                      value={b.text}
                      onChange={(e) => setForm((f) => {
                        const arr = [...f.buttons]; arr[idx] = { ...arr[idx], text: e.target.value }; return { ...f, buttons: arr };
                      })}
                    />
                    <button
                      type="button"
                      className="shrink-0 px-2 text-gray-400 hover:text-red-500"
                      onClick={() => setForm((f) => ({ ...f, buttons: f.buttons.filter((_, i) => i !== idx) }))}
                    >
                      ✕
                    </button>
                  </div>
                  <input
                    className="block w-full px-2 py-1.5 text-sm rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800 text-gray-900 dark:text-gray-100"
                    placeholder="https://"
                    value={b.url}
                    onChange={(e) => setForm((f) => {
                      const arr = [...f.buttons]; arr[idx] = { ...arr[idx], url: e.target.value }; return { ...f, buttons: arr };
                    })}
                  />
                </div>
              ))}
            </div>

            {error && <p className="text-sm text-red-500">{error}</p>}
            <Button onClick={requestSend} disabled={sending || uploading || !canSend}>
              {sending ? t("broadcast.sending") : form.scheduled_at ? t("broadcast.schedule_btn") : t("broadcast.send")}
            </Button>
          </div>
        </div>

        {/* Right: history — scrollable */}
        <div className="flex-1 min-w-0 flex flex-col min-h-0">
          <div className="flex items-center justify-between mb-3 shrink-0 gap-3">
            <h2 className="font-medium text-gray-900 dark:text-gray-100">{t("broadcast.history")}</h2>
            <label className="flex items-center gap-2 text-xs text-gray-500 dark:text-gray-400">
              <span>{t("broadcast.per_page")}</span>
              <select
                value={historyLimit}
                onChange={(e) => {
                  setHistoryOffset(0);
                  setHistoryLimit(parseInt(e.target.value));
                }}
                className="px-2 py-1 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 text-xs focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {PAGE_SIZE_OPTIONS.map((n) => (
                  <option key={n} value={n}>{n}</option>
                ))}
              </select>
            </label>
          </div>
          {loading ? (
            <div className="flex justify-center py-8"><Spinner /></div>
          ) : history.length === 0 ? (
            <p className="text-sm text-gray-500 dark:text-gray-400">{t("broadcast.no_history")}</p>
          ) : (
            <>
              <div className="flex-1 min-h-0 overflow-y-auto space-y-3 pr-1 -mr-1">
                {history.map((b) => (
                  <BroadcastRow
                    key={b.id}
                    b={b}
                    t={t}
                    onCancel={() => setActionModal({ kind: "cancel", broadcast: b, loading: false, error: "" })}
                    onDelete={() => setActionModal({ kind: "delete", broadcast: b, loading: false, error: "" })}
                  />
                ))}
              </div>
              {historyTotal > historyLimit && (() => {
                const totalPages = Math.ceil(historyTotal / historyLimit);
                const currentPage = Math.floor(historyOffset / historyLimit) + 1;
                const goTo = (page) => setHistoryOffset((page - 1) * historyLimit);
                const pages = getPageRange(currentPage, totalPages);
                return (
                  <div className="shrink-0 pt-4 mt-2 border-t border-gray-200 dark:border-gray-700 flex flex-col items-center gap-2">
                    <nav className="flex items-center gap-1">
                      <button
                        type="button"
                        disabled={currentPage === 1}
                        onClick={() => goTo(currentPage - 1)}
                        aria-label="Previous page"
                        className="w-8 h-8 inline-flex items-center justify-center rounded-md text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                      >
                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                        </svg>
                      </button>
                      {pages.map((p, idx) =>
                        p === "…" ? (
                          <span key={`ellipsis-${idx}`} className="w-8 h-8 inline-flex items-center justify-center text-xs text-gray-400">…</span>
                        ) : (
                          <button
                            key={p}
                            type="button"
                            onClick={() => goTo(p)}
                            aria-current={p === currentPage ? "page" : undefined}
                            className={`w-8 h-8 inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors ${
                              p === currentPage
                                ? "bg-blue-600 text-white shadow-sm"
                                : "text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700"
                            }`}
                          >
                            {p}
                          </button>
                        )
                      )}
                      <button
                        type="button"
                        disabled={currentPage === totalPages}
                        onClick={() => goTo(currentPage + 1)}
                        aria-label="Next page"
                        className="w-8 h-8 inline-flex items-center justify-center rounded-md text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                      >
                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                        </svg>
                      </button>
                    </nav>
                    <span className="text-xs text-gray-400 dark:text-gray-500">
                      {t("broadcast.pagination_range", {
                        from: historyOffset + 1,
                        to: Math.min(historyOffset + history.length, historyTotal),
                        total: historyTotal,
                      })}
                    </span>
                  </div>
                );
              })()}
            </>
          )}
        </div>
      </div>

      <Modal
        open={!!confirm}
        onClose={() => setConfirm(null)}
        title={t("broadcast.confirm_title")}
        size="sm"
      >
        <p className="text-sm text-gray-600 dark:text-gray-300 mb-4">
          {t("broadcast.confirm_body", {
            count: confirm?.count ?? 0,
            bot: confirm?.botName ?? "",
          })}
        </p>
        <div className="flex gap-2 justify-end">
          <Button variant="secondary" onClick={() => setConfirm(null)} disabled={sending}>
            {t("broadcast.cancel")}
          </Button>
          <Button onClick={confirmSend} disabled={sending}>
            {sending ? t("broadcast.sending") : t("broadcast.confirm_send")}
          </Button>
        </div>
      </Modal>

      <Modal
        open={!!actionModal}
        onClose={() => !actionModal?.loading && setActionModal(null)}
        title={
          actionModal?.kind === "cancel"
            ? t("broadcast.cancel_modal_title")
            : t("broadcast.delete_title")
        }
        size="sm"
      >
        <p className="text-sm text-gray-600 dark:text-gray-300 mb-2">
          {actionModal?.kind === "cancel"
            ? t("broadcast.cancel_modal_body")
            : t("broadcast.delete_body")}
        </p>
        {actionModal?.error && (
          <p className="text-sm text-red-500 mb-3">{actionModal.error}</p>
        )}
        <div className="flex gap-2 justify-end mt-4">
          <Button
            variant="secondary"
            onClick={() => setActionModal(null)}
            disabled={actionModal?.loading}
          >
            {t("broadcast.keep")}
          </Button>
          <Button
            variant="danger"
            onClick={runAction}
            disabled={actionModal?.loading}
          >
            {actionModal?.loading
              ? actionModal.kind === "cancel"
                ? t("broadcast.canceling")
                : t("broadcast.deleting")
              : actionModal?.kind === "cancel"
                ? t("broadcast.confirm_cancel_yes")
                : t("broadcast.confirm_delete")}
          </Button>
        </div>
      </Modal>
    </Layout>
  );
}

function BroadcastRow({ b, t, onCancel, onDelete }) {
  const statusKey = `broadcast.status_${b.status}`;
  const progress = b.total_recipients > 0 ? (b.sent_count / b.total_recipients) * 100 : 0;
  const isScheduled = b.status === "scheduled";
  const isDeletable = TERMINAL_STATUSES.has(b.status);
  const hasText = Boolean(b.text && b.text.trim());

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4">
      <div className="flex items-start justify-between gap-3 mb-2">
        {hasText ? (
          <p className="text-sm text-gray-700 dark:text-gray-300 line-clamp-2 flex-1 whitespace-pre-wrap break-words">{b.text}</p>
        ) : (
          <p className="text-sm italic text-gray-400 dark:text-gray-500 flex-1">
            {t("broadcast.media_only", { type: b.media_type || "media" })}
          </p>
        )}
        <Badge color={STATUS_COLORS[b.status] || "gray"}>{t(statusKey)}</Badge>
      </div>

      {isScheduled && (
        <div className="flex items-center justify-between gap-2 text-xs">
          <span className="text-gray-500 dark:text-gray-400">
            {t("broadcast.scheduled_for", { time: formatDateTime(b.scheduled_at) })}
          </span>
          <button
            type="button"
            onClick={onCancel}
            className="text-red-500 hover:text-red-600 hover:underline"
          >
            {t("broadcast.cancel_scheduled")}
          </button>
        </div>
      )}

      {(b.status === "sending" || b.status === "sent") && b.total_recipients > 0 && (
        <div className="space-y-1">
          <div className="flex justify-between text-xs text-gray-500 dark:text-gray-400">
            <span>{t("broadcast.progress", { sent: b.sent_count, total: b.total_recipients })}</span>
            {b.failed_count > 0 && (
              <span className="text-red-500">{t("broadcast.failed_count", { count: b.failed_count })}</span>
            )}
          </div>
          <div className="h-1.5 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
            <div
              className="h-full bg-blue-500 rounded-full transition-all duration-500"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
      )}

      {!isScheduled && (
        <div className="flex items-center justify-between gap-2 mt-2">
          <p className="text-xs text-gray-400">{formatDateTime(b.created_at)}</p>
          {isDeletable && (
            <button
              type="button"
              onClick={onDelete}
              className="text-xs text-gray-400 hover:text-red-500 transition-colors"
              aria-label={t("broadcast.delete")}
              title={t("broadcast.delete")}
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6M1 7h22M9 7V4a1 1 0 011-1h4a1 1 0 011 1v3" />
              </svg>
            </button>
          )}
        </div>
      )}
    </div>
  );
}
