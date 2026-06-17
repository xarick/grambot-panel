import { useTranslation } from "@/hooks/useTranslation.jsx";
import { Layout } from "@/components/layout/Layout.jsx";
import { StatsPanel } from "@/components/StatsPanel.jsx";

export function DashboardPage() {
  const { t } = useTranslation();

  return (
    <Layout>
      <div className="p-6 max-w-5xl mx-auto">
        <h1 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-6">
          {t("dashboard.title")}
        </h1>
        <StatsPanel />
      </div>
    </Layout>
  );
}
