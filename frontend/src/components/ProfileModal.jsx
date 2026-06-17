import { useEffect, useState } from "react";
import * as authApi from "@/api/auth.js";
import { useAuth } from "@/hooks/useAuth.jsx";
import { useTranslation } from "@/hooks/useTranslation.jsx";
import { Modal } from "@/components/ui/Modal.jsx";
import { Input } from "@/components/ui/Input.jsx";
import { Button } from "@/components/ui/Button.jsx";

export function ProfileModal({ open, onClose }) {
  const { user, setUser } = useAuth();
  const { t } = useTranslation();
  const [form, setForm] = useState({ username: "", current_password: "", new_password: "", confirm: "" });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [savedOk, setSavedOk] = useState(false);

  useEffect(() => {
    if (!open) return;
    setForm({ username: user?.username || "", current_password: "", new_password: "", confirm: "" });
    setError("");
    setSavedOk(false);
  }, [open, user]);

  const save = async () => {
    setError("");
    setSavedOk(false);

    if (form.new_password) {
      if (form.new_password !== form.confirm) {
        setError(t("profile.password_mismatch"));
        return;
      }
      if (!form.current_password) {
        setError(t("profile.current_required"));
        return;
      }
    }

    const payload = {};
    if (form.username && form.username !== user?.username) payload.username = form.username;
    if (form.new_password) {
      payload.current_password = form.current_password;
      payload.new_password = form.new_password;
    }
    if (Object.keys(payload).length === 0) {
      onClose();
      return;
    }

    setSaving(true);
    try {
      const updated = await authApi.updateProfile(payload);
      setUser(updated);
      setSavedOk(true);
      setForm((f) => ({ ...f, current_password: "", new_password: "", confirm: "" }));
    } catch (err) {
      setError(err.detail || t("common.error"));
    } finally {
      setSaving(false);
    }
  };

  return (
    <Modal open={open} onClose={onClose} title={t("profile.title")} size="sm">
      <div className="space-y-4">
        <Input
          label={t("profile.username")}
          value={form.username}
          autoComplete="username"
          onChange={(e) => setForm((f) => ({ ...f, username: e.target.value }))}
        />

        <div className="border-t border-gray-200 dark:border-gray-700 pt-4 space-y-4">
          <p className="text-xs text-gray-500 dark:text-gray-400">{t("profile.password_section")}</p>
          <Input
            label={t("profile.current_password")}
            type="password"
            value={form.current_password}
            autoComplete="current-password"
            onChange={(e) => setForm((f) => ({ ...f, current_password: e.target.value }))}
          />
          <Input
            label={t("profile.new_password")}
            type="password"
            value={form.new_password}
            autoComplete="new-password"
            onChange={(e) => setForm((f) => ({ ...f, new_password: e.target.value }))}
          />
          <Input
            label={t("profile.confirm_password")}
            type="password"
            value={form.confirm}
            autoComplete="new-password"
            onChange={(e) => setForm((f) => ({ ...f, confirm: e.target.value }))}
          />
        </div>

        {error && <p className="text-sm text-red-500">{error}</p>}
        {savedOk && <p className="text-sm text-green-600 dark:text-green-400">{t("profile.saved")}</p>}

        <div className="flex justify-end gap-2 pt-1">
          <Button variant="secondary" onClick={onClose} disabled={saving}>
            {t("profile.cancel")}
          </Button>
          <Button onClick={save} disabled={saving}>
            {saving ? t("common.loading") : t("profile.save")}
          </Button>
        </div>
      </div>
    </Modal>
  );
}
