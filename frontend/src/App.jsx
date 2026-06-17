import { useEffect, useState } from "react";
import { Navigate, Route, Routes, useLocation } from "react-router-dom";
import { loginPath } from "@/api/auth.js";
import { useAuth } from "@/hooks/useAuth.jsx";
import { Spinner } from "@/components/ui/Spinner.jsx";

import { LoginPage } from "@/pages/LoginPage.jsx";
import { DashboardPage } from "@/pages/DashboardPage.jsx";
import { BotsPage } from "@/pages/BotsPage.jsx";
import { InboxPage } from "@/pages/InboxPage.jsx";
import { BroadcastPage } from "@/pages/BroadcastPage.jsx";
import { TemplatesPage } from "@/pages/TemplatesPage.jsx";
import { ChannelsPage } from "@/pages/ChannelsPage.jsx";
import { ChannelChatsPage } from "@/pages/ChannelChatsPage.jsx";
import { ChannelDetailPage } from "@/pages/ChannelDetailPage.jsx";
import { UsersPage } from "@/pages/UsersPage.jsx";

function ProtectedRoute({ children, superadminOnly = false }) {
  const { user } = useAuth();
  const location = useLocation();

  if (user === undefined) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-950">
        <Spinner size="lg" />
      </div>
    );
  }

  if (user === null) {
    return <Navigate to={window.__LOGIN_PATH__ || "/manage/login"} state={{ from: location }} replace />;
  }

  if (superadminOnly && !user.is_superuser) {
    return <Navigate to="/dashboard" replace />;
  }

  return children;
}

export function App() {
  const [loginPathLoaded, setLoginPathLoaded] = useState(false);
  const [dynamicLoginPath, setDynamicLoginPath] = useState("/manage/login");

  useEffect(() => {
    loginPath()
      .then(({ path }) => {
        window.__LOGIN_PATH__ = path;
        setDynamicLoginPath(path);
      })
      .catch(() => {})
      .finally(() => setLoginPathLoaded(true));
  }, []);

  if (!loginPathLoaded) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-950">
        <Spinner size="lg" />
      </div>
    );
  }

  return (
    <Routes>
      <Route path={dynamicLoginPath} element={<LoginPage />} />
      <Route
        path="/dashboard"
        element={<ProtectedRoute><DashboardPage /></ProtectedRoute>}
      />
      <Route
        path="/bots"
        element={<ProtectedRoute><BotsPage /></ProtectedRoute>}
      />
      <Route
        path="/bots/:botId/conversations"
        element={<ProtectedRoute><InboxPage /></ProtectedRoute>}
      />
      <Route
        path="/broadcast"
        element={<ProtectedRoute><BroadcastPage /></ProtectedRoute>}
      />
      <Route
        path="/templates"
        element={<ProtectedRoute><TemplatesPage /></ProtectedRoute>}
      />
      <Route
        path="/channels"
        element={<ProtectedRoute><ChannelsPage /></ProtectedRoute>}
      />
      <Route
        path="/channels/:botId"
        element={<ProtectedRoute><ChannelChatsPage /></ProtectedRoute>}
      />
      <Route
        path="/channels/:botId/:chatRowId"
        element={<ProtectedRoute><ChannelDetailPage /></ProtectedRoute>}
      />
      <Route
        path="/users"
        element={<ProtectedRoute superadminOnly><UsersPage /></ProtectedRoute>}
      />
      <Route path="*" element={<div className="min-h-screen flex items-center justify-center text-gray-900 dark:text-gray-100 text-2xl font-mono">404</div>} />
    </Routes>
  );
}
