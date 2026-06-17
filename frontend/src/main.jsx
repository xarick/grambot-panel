import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import { AuthProvider } from "@/hooks/useAuth.jsx";
import { ThemeProvider } from "@/hooks/useTheme.jsx";
import { TranslationProvider } from "@/hooks/useTranslation.jsx";
import { App } from "./App.jsx";
import "./index.css";

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <BrowserRouter>
      <ThemeProvider>
        <TranslationProvider>
          <AuthProvider>
            <App />
          </AuthProvider>
        </TranslationProvider>
      </ThemeProvider>
    </BrowserRouter>
  </React.StrictMode>
);
