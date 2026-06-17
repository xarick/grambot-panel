import { useEffect, useState } from "react";
import * as usersApi from "@/api/users.js";
import { useAuth } from "@/hooks/useAuth.jsx";
import { useTranslation } from "@/hooks/useTranslation.jsx";
import { Layout } from "@/components/layout/Layout.jsx";
import { Button } from "@/components/ui/Button.jsx";
import { Input, Select } from "@/components/ui/Input.jsx";
import { Modal } from "@/components/ui/Modal.jsx";
import { Badge } from "@/components/ui/Badge.jsx";
import { Spinner } from "@/components/ui/Spinner.jsx";
import { formatDateTime } from "@/utils/format.js";

const ICONS = {
  view: "M15 12a3 3 0 11-6 0 3 3 0 016 0z M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z",
  edit: "M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z",
  delete: "M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16",
};

function IconBtn({ d, label, onClick, danger }) {
  return (
    <button
      onClick={onClick}
      aria-label={label}
      title={label}
      className={`p-1.5 text-gray-400 transition-colors ${
        danger ? "hover:text-red-500" : "hover:text-blue-500"
      }`}
    >
      <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        {d.split(" M").map((seg, i) => (
          <path key={i} strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={i ? "M" + seg : seg} />
        ))}
      </svg>
    </button>
  );
}

export function UsersPage() {
  const { user: currentUser } = useAuth();
  const { t } = useTranslation();
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [addOpen, setAddOpen] = useState(false);
  const [editTarget, setEditTarget] = useState(null);
  const [showTarget, setShowTarget] = useState(null);
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [form, setForm] = useState({ username: "", password: "", is_superuser: false });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const isEdit = !!editTarget;
  const formOpen = addOpen || isEdit;

  const load = async () => {
    const data = await usersApi.list();
    setUsers(data);
    setLoading(false);
  };

  useEffect(() => { load(); }, []);

  const openAdd = () => {
    setForm({ username: "", password: "", is_superuser: false });
    setError("");
    setEditTarget(null);
    setAddOpen(true);
  };

  const openEdit = (u) => {
    setForm({ username: u.username, password: "", is_superuser: u.is_superuser });
    setError("");
    setAddOpen(false);
    setEditTarget(u);
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
        const payload = { username: form.username, is_superuser: form.is_superuser };
        if (form.password) payload.password = form.password;
        await usersApi.update(editTarget.id, payload);
      } else {
        await usersApi.create(form);
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
    await usersApi.remove(deleteTarget.id);
    setDeleteTarget(null);
    await load();
  };

  return (
    <Layout>
      <div className="p-6 max-w-5xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-xl font-semibold text-gray-900 dark:text-gray-100">{t("users.title")}</h1>
          <Button size="sm" onClick={openAdd}>
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            {t("users.add")}
          </Button>
        </div>

        {loading ? (
          <div className="flex justify-center py-16"><Spinner size="lg" /></div>
        ) : users.length === 0 ? (
          <p className="text-center py-16 text-gray-500 dark:text-gray-400 text-sm">{t("users.no_users")}</p>
        ) : (
          <div className="overflow-x-auto bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-200 dark:border-gray-700 text-left text-xs font-medium uppercase tracking-wide text-gray-500 dark:text-gray-400">
                  <th className="px-4 py-3 w-12">{t("users.id")}</th>
                  <th className="px-4 py-3">{t("users.username")}</th>
                  <th className="px-4 py-3">{t("users.role")}</th>
                  <th className="px-4 py-3">{t("users.status")}</th>
                  <th className="px-4 py-3">{t("users.created_at")}</th>
                  <th className="px-4 py-3 text-right">{t("users.actions")}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
                {users.map((u) => (
                  <tr key={u.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/40">
                    <td className="px-4 py-3 text-gray-400 tabular-nums">{u.id}</td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 shrink-0 rounded-full bg-blue-100 dark:bg-blue-900/40 flex items-center justify-center text-blue-600 dark:text-blue-400 text-sm font-semibold">
                          {u.username[0]?.toUpperCase()}
                        </div>
                        <span className="font-medium text-gray-900 dark:text-gray-100">
                          {u.username}
                          {u.id === currentUser?.id && (
                            <span className="ml-2 text-xs text-gray-400">({t("users.you")})</span>
                          )}
                        </span>
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <Badge color={u.is_superuser ? "purple" : "gray"}>
                        {u.is_superuser ? t("users.role_superadmin") : t("users.role_admin")}
                      </Badge>
                    </td>
                    <td className="px-4 py-3">
                      <Badge color={u.is_active ? "green" : "gray"}>
                        {u.is_active ? t("users.active") : t("users.inactive")}
                      </Badge>
                    </td>
                    <td className="px-4 py-3 text-gray-500 dark:text-gray-400 whitespace-nowrap">
                      {formatDateTime(u.created_at)}
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center justify-end gap-1">
                        <IconBtn d={ICONS.view} label={t("users.view")} onClick={() => setShowTarget(u)} />
                        <IconBtn d={ICONS.edit} label={t("users.edit")} onClick={() => openEdit(u)} />
                        {u.id !== currentUser?.id && (
                          <IconBtn d={ICONS.delete} label={t("users.delete")} danger onClick={() => setDeleteTarget(u)} />
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <Modal open={formOpen} onClose={closeForm} title={isEdit ? t("users.edit") : t("users.add")}>
        <div className="space-y-4">
          <Input
            label={t("users.username")}
            value={form.username}
            onChange={(e) => setForm((f) => ({ ...f, username: e.target.value }))}
            autoComplete="off"
          />
          <Input
            label={t("users.password")}
            type="password"
            value={form.password}
            onChange={(e) => setForm((f) => ({ ...f, password: e.target.value }))}
            autoComplete="new-password"
          />
          {isEdit && <p className="-mt-2 text-xs text-gray-500 dark:text-gray-400">{t("users.password_hint")}</p>}
          <Select
            label={t("users.role")}
            value={form.is_superuser ? "superadmin" : "admin"}
            onChange={(e) => setForm((f) => ({ ...f, is_superuser: e.target.value === "superadmin" }))}
          >
            <option value="admin">{t("users.role_admin")}</option>
            <option value="superadmin">{t("users.role_superadmin")}</option>
          </Select>
          {error && <p className="text-sm text-red-500">{error}</p>}
          <div className="flex gap-2 justify-end pt-2">
            <Button variant="secondary" onClick={closeForm}>{t("users.cancel")}</Button>
            <Button onClick={handleSave} disabled={saving}>
              {saving ? t("common.loading") : t("users.save")}
            </Button>
          </div>
        </div>
      </Modal>

      <Modal open={!!showTarget} onClose={() => setShowTarget(null)} title={t("users.details")} size="sm">
        {showTarget && (
          <div className="space-y-3">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-full bg-blue-100 dark:bg-blue-900/40 flex items-center justify-center text-blue-600 dark:text-blue-400 text-lg font-semibold">
                {showTarget.username[0]?.toUpperCase()}
              </div>
              <div>
                <div className="font-semibold text-gray-900 dark:text-gray-100">{showTarget.username}</div>
                <Badge color={showTarget.is_superuser ? "purple" : "gray"}>
                  {showTarget.is_superuser ? t("users.role_superadmin") : t("users.role_admin")}
                </Badge>
              </div>
            </div>
            <dl className="text-sm divide-y divide-gray-100 dark:divide-gray-700">
              {[
                [t("users.id"), showTarget.id],
                [t("users.status"), showTarget.is_active ? t("users.active") : t("users.inactive")],
                [t("users.created_at"), formatDateTime(showTarget.created_at)],
              ].map(([k, v]) => (
                <div key={k} className="flex justify-between py-2">
                  <dt className="text-gray-500 dark:text-gray-400">{k}</dt>
                  <dd className="font-medium text-gray-900 dark:text-gray-100">{v}</dd>
                </div>
              ))}
            </dl>
            <div className="flex justify-end pt-1">
              <Button variant="secondary" onClick={() => setShowTarget(null)}>{t("users.close")}</Button>
            </div>
          </div>
        )}
      </Modal>

      <Modal open={!!deleteTarget} onClose={() => setDeleteTarget(null)} title={t("users.delete")} size="sm">
        <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">{t("users.confirm_delete")}</p>
        <div className="flex gap-2 justify-end">
          <Button variant="secondary" onClick={() => setDeleteTarget(null)}>{t("users.cancel")}</Button>
          <Button variant="danger" onClick={handleDelete}>{t("users.delete")}</Button>
        </div>
      </Modal>
    </Layout>
  );
}
