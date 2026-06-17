import { useEffect, useState } from "react";
import * as automationApi from "@/api/automation.js";
import { useTranslation } from "@/hooks/useTranslation.jsx";
import { Modal } from "@/components/ui/Modal.jsx";
import { Button } from "@/components/ui/Button.jsx";
import { Input, Textarea, Select } from "@/components/ui/Input.jsx";

export function AutomationModal({ bot, open, onClose }) {
  const { t } = useTranslation();
  const [welcome, setWelcomeText] = useState("");
  const [replies, setReplies] = useState([]);
  const [draft, setDraft] = useState({ keyword: "", response: "", match_mode: "contains" });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [savedOk, setSavedOk] = useState(false);

  useEffect(() => {
    if (!open || !bot) return;
    setError("");
    setSavedOk(false);
    automationApi.getWelcome(bot.id).then((d) => setWelcomeText(d.welcome_message || "")).catch(() => {});
    automationApi.listReplies(bot.id).then(setReplies).catch(() => {});
  }, [open, bot]);

  const saveWelcome = async () => {
    setBusy(true);
    setError("");
    try {
      await automationApi.setWelcome(bot.id, welcome);
      setSavedOk(true);
    } catch (e) {
      setError(e.detail || t("common.error"));
    } finally {
      setBusy(false);
    }
  };

  const addReply = async () => {
    if (!draft.keyword.trim() || !draft.response.trim()) return;
    setBusy(true);
    setError("");
    try {
      await automationApi.createReply({ bot_id: bot.id, ...draft });
      setDraft({ keyword: "", response: "", match_mode: "contains" });
      setReplies(await automationApi.listReplies(bot.id));
    } catch (e) {
      setError(e.detail || t("common.error"));
    } finally {
      setBusy(false);
    }
  };

  const removeReply = async (id) => {
    await automationApi.deleteReply(id);
    setReplies(await automationApi.listReplies(bot.id));
  };

  return (
    <Modal open={open} onClose={onClose} title={`${t("automation.title")} — ${bot?.name || ""}`} size="lg">
      <div className="space-y-5">
        <div>
          <Textarea
            label={t("automation.welcome")}
            rows={3}
            value={welcome}
            placeholder={t("automation.welcome_ph")}
            onChange={(e) => { setWelcomeText(e.target.value); setSavedOk(false); }}
          />
          <div className="mt-2 flex items-center gap-3">
            <Button size="sm" onClick={saveWelcome} disabled={busy}>{t("automation.save_welcome")}</Button>
            {savedOk && <span className="text-sm text-green-600 dark:text-green-400">{t("automation.saved")}</span>}
          </div>
        </div>

        <div className="border-t border-gray-200 dark:border-gray-700 pt-4">
          <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100 mb-3">{t("automation.replies")}</h3>

          <div className="space-y-2 mb-4">
            {replies.length === 0 && (
              <p className="text-sm text-gray-500 dark:text-gray-400">{t("automation.no_replies")}</p>
            )}
            {replies.map((r) => (
              <div key={r.id} className="flex items-start gap-3 rounded-lg border border-gray-200 dark:border-gray-700 p-3">
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-medium text-gray-900 dark:text-gray-100">
                    {r.keyword} <span className="text-xs text-gray-400">({r.match_mode})</span>
                  </div>
                  <div className="text-sm text-gray-500 dark:text-gray-400 break-words">{r.response}</div>
                </div>
                <button onClick={() => removeReply(r.id)} className="text-gray-400 hover:text-red-500" aria-label={t("automation.delete")}>
                  ✕
                </button>
              </div>
            ))}
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            <Input
              label={t("automation.keyword")}
              value={draft.keyword}
              onChange={(e) => setDraft((d) => ({ ...d, keyword: e.target.value }))}
            />
            <Select
              label={t("automation.match")}
              value={draft.match_mode}
              onChange={(e) => setDraft((d) => ({ ...d, match_mode: e.target.value }))}
            >
              <option value="contains">{t("automation.match_contains")}</option>
              <option value="exact">{t("automation.match_exact")}</option>
            </Select>
          </div>
          <div className="mt-2">
            <Textarea
              label={t("automation.response")}
              rows={2}
              value={draft.response}
              onChange={(e) => setDraft((d) => ({ ...d, response: e.target.value }))}
            />
          </div>
          {error && <p className="text-sm text-red-500 mt-2">{error}</p>}
          <div className="mt-3 flex justify-end">
            <Button size="sm" onClick={addReply} disabled={busy}>{t("automation.add")}</Button>
          </div>
        </div>
      </div>
    </Modal>
  );
}
