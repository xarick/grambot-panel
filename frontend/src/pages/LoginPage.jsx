import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@/hooks/useAuth.jsx";
import { useTranslation } from "@/hooks/useTranslation.jsx";
import { Button } from "@/components/ui/Button.jsx";
import { Input } from "@/components/ui/Input.jsx";

export function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const { t } = useTranslation();
  const [form, setForm] = useState({ username: "", password: "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await login(form.username, form.password);
      navigate("/dashboard");
    } catch (err) {
      setError(err.detail || t("auth.invalid_credentials"));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-950 p-4">
      <div className="w-full max-w-sm">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-2xl bg-blue-600 text-white font-bold text-xl mb-4">
            TG
          </div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">tg-panel</h1>
        </div>

        <form
          onSubmit={submit}
          className="bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-200 dark:border-gray-700 p-6 space-y-4"
        >
          <Input
            label={t("auth.username")}
            type="text"
            autoComplete="username"
            value={form.username}
            onChange={(e) => setForm((f) => ({ ...f, username: e.target.value }))}
            required
          />
          <Input
            label={t("auth.password")}
            type="password"
            autoComplete="current-password"
            value={form.password}
            onChange={(e) => setForm((f) => ({ ...f, password: e.target.value }))}
            required
          />
          {error && (
            <p className="text-sm text-red-500 bg-red-50 dark:bg-red-900/20 px-3 py-2 rounded-lg">
              {error}
            </p>
          )}
          <Button type="submit" className="w-full" disabled={loading}>
            {loading ? t("auth.signing_in") : t("auth.login")}
          </Button>
        </form>

        <p className="mt-6 text-center text-xs text-gray-400 dark:text-gray-600">
          Developed by{" "}
          <a
            href="https://itone.uz"
            target="_blank"
            rel="noopener noreferrer"
            className="font-semibold text-gray-500 transition-colors hover:text-blue-600 dark:text-gray-400 dark:hover:text-blue-400"
          >
            itone.uz
          </a>
        </p>
      </div>
    </div>
  );
}
