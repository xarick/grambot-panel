import { useEffect, useState } from "react";
import * as templatesApi from "@/api/templates.js";
import { useTranslation } from "@/hooks/useTranslation.jsx";
import { Layout } from "@/components/layout/Layout.jsx";
import { Button } from "@/components/ui/Button.jsx";
import { Input, Textarea } from "@/components/ui/Input.jsx";
import { Modal } from "@/components/ui/Modal.jsx";
import { Spinner } from "@/components/ui/Spinner.jsx";

export function TemplatesPage() {
  const { t } = useTranslation();
  const [templates, setTemplates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [addOpen, setAddOpen] = useState(false);
  const [editTarget, setEditTarget] = useState(null);
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [form, setForm] = useState({ title: "", text: "" });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const isEdit = !!editTarget;
  const formOpen = addOpen || isEdit;

  const load = async () => {
    const data = await templatesApi.list();
    setTemplates(data);
    setLoading(false);
  };

  useEffect(() => { load(); }, []);

  const openAdd = () => {
    setForm({ title: "", text: "" });
    setError("");
    setEditTarget(null);
    setAddOpen(true);
  };

  const openEdit = (tpl) => {
    setForm({ title: tpl.title, text: tpl.text });
    setError("");
    setAddOpen(false);
    setEditTarget(tpl);
  };

  const closeForm = () => {
    setAddOpen(false);
    setEditTarget(null);
  };

  const handleSave = async () => {
    setSaving(true);
    setError("");
    try {
      if (isEdit) {
        await templatesApi.update(editTarget.id, form);
      } else {
        await templatesApi.create(form);
      }
      closeForm();
      await load();
    } catch (err) {
      setError(err.detail || t("common.error"));
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!deleteTarget) return;
    await templatesApi.remove(deleteTarget.id);
    setDeleteTarget(null);
    await load();
  };

  return (
    <Layout>
      <div className="p-6 max-w-5xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-xl font-semibold text-gray-900 dark:text-gray-100">{t("templates.title")}</h1>
          <Button size="sm" onClick={openAdd}>
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            {t("templates.add")}
          </Button>
        </div>

        {loading ? (
          <div className="flex justify-center py-16"><Spinner size="lg" /></div>
        ) : templates.length === 0 ? (
          <p className="text-center py-16 text-gray-500 dark:text-gray-400 text-sm">{t("templates.no_templates")}</p>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 items-stretch">
            {templates.map((tpl) => (
              <div
                key={tpl.id}
                className="h-full bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4 flex gap-3"
              >
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-gray-900 dark:text-gray-100 mb-1 break-words">{tpl.title}</p>
                  <p className="text-sm text-gray-500 dark:text-gray-400 whitespace-pre-wrap break-words">{tpl.text}</p>
                </div>
                <div className="flex shrink-0 flex-col gap-1">
                  <button
                    onClick={() => openEdit(tpl)}
                    className="text-gray-400 hover:text-blue-500 dark:hover:text-blue-400 transition-colors"
                    aria-label={t("templates.edit")}
                    title={t("templates.edit")}
                  >
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                    </svg>
                  </button>
                  <button
                    onClick={() => setDeleteTarget(tpl)}
                    className="text-gray-400 hover:text-red-500 dark:hover:text-red-400 transition-colors"
                    aria-label={t("templates.delete")}
                    title={t("templates.delete")}
                  >
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <Modal open={formOpen} onClose={closeForm} title={isEdit ? t("templates.edit") : t("templates.add")}>
        <div className="space-y-4">
          <Input
            label={t("templates.title_field")}
            value={form.title}
            onChange={(e) => setForm((f) => ({ ...f, title: e.target.value }))}
          />
          <Textarea
            label={t("templates.text_field")}
            rows={4}
            value={form.text}
            onChange={(e) => setForm((f) => ({ ...f, text: e.target.value }))}
          />
          {error && <p className="text-sm text-red-500">{error}</p>}
          <div className="flex gap-2 justify-end pt-2">
            <Button variant="secondary" onClick={closeForm}>{t("templates.cancel")}</Button>
            <Button onClick={handleSave} disabled={saving}>
              {saving ? t("common.loading") : t("templates.save")}
            </Button>
          </div>
        </div>
      </Modal>

      <Modal open={!!deleteTarget} onClose={() => setDeleteTarget(null)} title={t("templates.delete")} size="sm">
        <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">{t("templates.confirm_delete")}</p>
        <div className="flex gap-2 justify-end">
          <Button variant="secondary" onClick={() => setDeleteTarget(null)}>{t("templates.cancel")}</Button>
          <Button variant="danger" onClick={handleDelete}>{t("templates.delete")}</Button>
        </div>
      </Modal>
    </Layout>
  );
}
