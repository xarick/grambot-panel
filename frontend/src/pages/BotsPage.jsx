import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import * as botsApi from "@/api/bots.js";
import { useAuth } from "@/hooks/useAuth.jsx";
import { useTranslation } from "@/hooks/useTranslation.jsx";
import { Layout } from "@/components/layout/Layout.jsx";
import { AutomationModal } from "@/components/AutomationModal.jsx";
import { Button } from "@/components/ui/Button.jsx";
import { Input } from "@/components/ui/Input.jsx";
import { Modal } from "@/components/ui/Modal.jsx";
import { Badge } from "@/components/ui/Badge.jsx";
import { Spinner } from "@/components/ui/Spinner.jsx";

export function BotsPage() {
  const { user } = useAuth();
  const { t } = useTranslation();
  const navigate = useNavigate();

  const [bots, setBots] = useState([]);
  const [loading, setLoading] = useState(true);
  const [addOpen, setAddOpen] = useState(false);
  const [editBot, setEditBot] = useState(null);
  const [deleteBot, setDeleteBot] = useState(null);
  const [automationBot, setAutomationBot] = useState(null);
  const [form, setForm] = useState({ name: "", token: "" });
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState("");

  const loadBots = async () => {
    try {
      const data = await botsApi.list();
      setBots(data);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadBots(); }, []);

  const openAdd = () => {
    setForm({ name: "", token: "" });
    setFormError("");
    setAddOpen(true);
  };

  const openEdit = (bot) => {
    setForm({ name: bot.name, token: bot.token, webhook_base_url: bot.webhook_base_url || "" });
    setFormError("");
    setEditBot(bot);
  };

  const handleSave = async () => {
    setSaving(true);
    setFormError("");
    try {
      if (editBot) {
        await botsApi.update(editBot.id, {
          name: form.name,
          webhook_base_url: form.webhook_base_url ?? "",
        });
        setEditBot(null);
      } else {
        await botsApi.create({ name: form.name, token: form.token });
        setAddOpen(false);
      }
      await loadBots();
    } catch (err) {
      setFormError(err.detail || t("common.error"));
    } finally {
      setSaving(false);
    }
  };

  const handleToggle = async (bot) => {
    try {
      await botsApi.update(bot.id, { is_active: !bot.is_active });
      await loadBots();
    } catch (err) {
      alert(err.detail);
    }
  };

  const handleDelete = async () => {
    if (!deleteBot) return;
    try {
      await botsApi.remove(deleteBot.id);
      setDeleteBot(null);
      await loadBots();
    } catch (err) {
      alert(err.detail);
    }
  };

  return (
    <Layout>
      <div className="p-6 max-w-5xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-xl font-semibold text-gray-900 dark:text-gray-100">{t("nav.bots")}</h1>
          {user?.is_superuser && (
            <Button onClick={openAdd} size="sm">
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              {t("dashboard.add_bot")}
            </Button>
          )}
        </div>

        {loading ? (
          <div className="flex justify-center py-20"><Spinner size="lg" /></div>
        ) : bots.length === 0 ? (
          <div className="text-center py-20 text-gray-500 dark:text-gray-400">{t("dashboard.no_bots")}</div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {bots.map((bot) => (
              <BotCard
                key={bot.id}
                bot={bot}
                isSuperuser={user?.is_superuser}
                onInbox={() => navigate(`/bots/${bot.id}/conversations`)}
                onEdit={() => openEdit(bot)}
                onDelete={() => setDeleteBot(bot)}
                onToggle={() => handleToggle(bot)}
                onAutomation={() => setAutomationBot(bot)}
                t={t}
              />
            ))}
          </div>
        )}
      </div>

      <Modal open={addOpen} onClose={() => setAddOpen(false)} title={t("dashboard.add_bot")}>
        <div className="space-y-4">
          <Input
            label={t("dashboard.bot_name")}
            value={form.name}
            onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
          />
          <Input
            label={t("dashboard.bot_token")}
            value={form.token}
            onChange={(e) => setForm((f) => ({ ...f, token: e.target.value }))}
            placeholder="1234567890:ABC..."
          />
          {formError && <p className="text-sm text-red-500">{formError}</p>}
          <div className="flex gap-2 justify-end pt-2">
            <Button variant="secondary" onClick={() => setAddOpen(false)}>
              {t("dashboard.cancel")}
            </Button>
            <Button onClick={handleSave} disabled={saving}>
              {saving ? t("common.loading") : t("dashboard.save")}
            </Button>
          </div>
        </div>
      </Modal>

      <Modal open={!!editBot} onClose={() => setEditBot(null)} title={t("dashboard.edit")}>
        <div className="space-y-4">
          <Input
            label={t("dashboard.bot_name")}
            value={form.name}
            onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
          />
          <div>
            <Input
              label={t("dashboard.webhook_url")}
              value={form.webhook_base_url || ""}
              placeholder={t("settings.placeholder")}
              onChange={(e) => setForm((f) => ({ ...f, webhook_base_url: e.target.value }))}
            />
            <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">{t("dashboard.webhook_hint")}</p>
          </div>
          {formError && <p className="text-sm text-red-500">{formError}</p>}
          <div className="flex gap-2 justify-end pt-2">
            <Button variant="secondary" onClick={() => setEditBot(null)}>
              {t("dashboard.cancel")}
            </Button>
            <Button onClick={handleSave} disabled={saving}>
              {saving ? t("common.loading") : t("dashboard.save")}
            </Button>
          </div>
        </div>
      </Modal>

      <Modal open={!!deleteBot} onClose={() => setDeleteBot(null)} title={t("dashboard.delete")} size="sm">
        <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">{t("dashboard.confirm_delete")}</p>
        <div className="flex gap-2 justify-end">
          <Button variant="secondary" onClick={() => setDeleteBot(null)}>
            {t("dashboard.cancel")}
          </Button>
          <Button variant="danger" onClick={handleDelete}>
            {t("dashboard.delete")}
          </Button>
        </div>
      </Modal>

      <AutomationModal
        bot={automationBot}
        open={!!automationBot}
        onClose={() => setAutomationBot(null)}
      />
    </Layout>
  );
}

function BotCard({ bot, isSuperuser, onInbox, onEdit, onDelete, onToggle, onAutomation, t }) {
  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5 space-y-4">
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <h2 className="font-semibold text-gray-900 dark:text-gray-100">{bot.name}</h2>
            <Badge color={bot.is_active ? "green" : "gray"}>
              {bot.is_active ? t("dashboard.active") : t("dashboard.inactive")}
            </Badge>
            {bot.webhook_base_url && (
              <span
                className="text-green-600 dark:text-green-500"
                title={`${t("dashboard.domain_on")} · ${bot.webhook_base_url}`}
                aria-label={t("dashboard.domain_on")}
              >
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 010 5.656l-3 3a4 4 0 01-5.656-5.656l1.5-1.5M10.172 13.828a4 4 0 010-5.656l3-3a4 4 0 015.656 5.656l-1.5 1.5" />
                </svg>
              </span>
            )}
          </div>
          <p className="text-xs text-gray-500 dark:text-gray-400">@{bot.username}</p>
        </div>
        {isSuperuser && (
          <div className="flex items-center gap-2">
            <button
              type="button"
              role="switch"
              aria-checked={bot.is_active}
              onClick={onToggle}
              title={bot.is_active ? t("dashboard.active") : t("dashboard.inactive")}
              aria-label={bot.is_active ? t("dashboard.active") : t("dashboard.inactive")}
              className={`relative inline-flex h-5 w-9 shrink-0 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500/40 ${
                bot.is_active ? "bg-green-500" : "bg-gray-300 dark:bg-gray-600"
              }`}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white shadow-sm transition-transform ${
                  bot.is_active ? "translate-x-[18px]" : "translate-x-0.5"
                }`}
              />
            </button>
            <button
              onClick={onAutomation}
              className="p-1.5 text-gray-400 hover:text-blue-500 transition-colors"
              title={t("dashboard.automation")}
              aria-label={t("dashboard.automation")}
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </button>
            <a
              href={`/api/v1/bots/${bot.id}/users.csv`}
              className="p-1.5 text-gray-400 hover:text-blue-500 transition-colors"
              title={t("dashboard.export")}
              aria-label={t("dashboard.export")}
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
              </svg>
            </a>
            <button onClick={onEdit} className="p-1.5 text-gray-400 hover:text-blue-500 transition-colors">
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
              </svg>
            </button>
            <button onClick={onDelete} className="p-1.5 text-gray-400 hover:text-red-500 transition-colors">
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
            </button>
          </div>
        )}
      </div>

      <div className="grid grid-cols-3 gap-3">
        {[
          { label: t("dashboard.subscribers"), value: bot.user_count },
          { label: t("dashboard.open_chats"), value: bot.open_conversation_count },
          { label: t("dashboard.unread"), value: bot.unread_count, highlight: bot.unread_count > 0 },
        ].map(({ label, value, highlight }) => (
          <div key={label} className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-3 text-center">
            <div className={`text-lg font-bold ${highlight ? "text-blue-600 dark:text-blue-400" : "text-gray-900 dark:text-gray-100"}`}>
              {value}
            </div>
            <div className="text-xs text-gray-500 dark:text-gray-400">{label}</div>
          </div>
        ))}
      </div>

      <Button size="sm" className="w-full" onClick={onInbox}>
        {t("dashboard.open_inbox")}
      </Button>
    </div>
  );
}
