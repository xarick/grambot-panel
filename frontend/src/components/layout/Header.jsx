import { useEffect, useRef, useState } from "react";
import { useLocation } from "react-router-dom";
import { useAuth } from "@/hooks/useAuth.jsx";
import { useTheme } from "@/hooks/useTheme.jsx";
import { useTranslation } from "@/hooks/useTranslation.jsx";
import { ProfileModal } from "@/components/ProfileModal.jsx";

const LANG_LABELS = { en: "EN", ru: "RU", uz: "UZ" };

function titleKeyFor(pathname) {
  if (pathname.startsWith("/dashboard")) return "nav.dashboard";
  if (pathname.includes("/conversations")) return "nav.inbox";
  if (pathname.startsWith("/bots")) return "nav.bots";
  if (pathname.startsWith("/broadcast")) return "nav.broadcast";
  if (pathname.startsWith("/templates")) return "nav.templates";
  if (pathname.startsWith("/channels")) return "nav.channels";
  if (pathname.startsWith("/users")) return "nav.users";
  return "nav.dashboard";
}

export function Header() {
  const { user, logout } = useAuth();
  const { dark, toggle } = useTheme();
  const { t, lang, setLanguage, supportedLangs } = useTranslation();
  const { pathname } = useLocation();
  const [menuOpen, setMenuOpen] = useState(false);
  const [profileOpen, setProfileOpen] = useState(false);
  const menuRef = useRef(null);

  useEffect(() => {
    if (!menuOpen) return;
    const onClick = (e) => {
      if (menuRef.current && !menuRef.current.contains(e.target)) setMenuOpen(false);
    };
    const onEsc = (e) => e.key === "Escape" && setMenuOpen(false);
    document.addEventListener("mousedown", onClick);
    document.addEventListener("keydown", onEsc);
    return () => {
      document.removeEventListener("mousedown", onClick);
      document.removeEventListener("keydown", onEsc);
    };
  }, [menuOpen]);

  return (
    <>
      <header className="sticky top-0 z-10 flex h-14 shrink-0 items-center justify-between border-b border-gray-200 bg-white/80 px-6 backdrop-blur dark:border-gray-800 dark:bg-gray-900/80">
        <h1 className="text-base font-semibold tracking-tight text-gray-900 dark:text-white">
          {t(titleKeyFor(pathname))}
        </h1>

        <div className="flex items-center gap-3">
          {/* Language segmented control */}
          <div className="flex items-center gap-0.5 rounded-lg bg-gray-100 p-0.5 dark:bg-gray-800">
            {supportedLangs.map((l) => (
              <button
                key={l}
                onClick={() => setLanguage(l)}
                aria-pressed={lang === l}
                className={`rounded-md px-2.5 py-1 text-xs font-semibold transition-colors ${
                  lang === l
                    ? "bg-white text-gray-900 shadow-sm dark:bg-gray-700 dark:text-white"
                    : "text-gray-500 hover:text-gray-800 dark:text-gray-400 dark:hover:text-gray-200"
                }`}
              >
                {LANG_LABELS[l]}
              </button>
            ))}
          </div>

          {/* Theme toggle */}
          <button
            onClick={toggle}
            className="rounded-lg p-2 text-gray-500 transition-colors hover:bg-gray-100 hover:text-gray-800 dark:text-gray-400 dark:hover:bg-gray-800 dark:hover:text-gray-200"
            aria-label="Toggle theme"
            title="Toggle theme"
          >
            {dark ? (
              <svg className="h-[18px] w-[18px]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364-6.364l-.707.707M6.343 17.657l-.707.707M18.364 17.657l-.707-.707M6.343 6.343l-.707-.707M12 8a4 4 0 100 8 4 4 0 000-8z" />
              </svg>
            ) : (
              <svg className="h-[18px] w-[18px]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
              </svg>
            )}
          </button>

          <div className="h-6 w-px bg-gray-200 dark:bg-gray-700" />

          {/* User menu */}
          <div className="relative" ref={menuRef}>
            <button
              onClick={() => setMenuOpen((o) => !o)}
              aria-haspopup="menu"
              aria-expanded={menuOpen}
              className="flex items-center gap-2.5 rounded-lg px-1.5 py-1 transition-colors hover:bg-gray-100 dark:hover:bg-gray-800"
            >
              <div className="flex h-8 w-8 items-center justify-center rounded-full bg-blue-600 text-xs font-semibold text-white">
                {user?.username?.[0]?.toUpperCase()}
              </div>
              <div className="hidden text-left leading-tight sm:block">
                <div className="text-sm font-medium text-gray-900 dark:text-gray-100">{user?.username}</div>
                {user?.is_superuser && (
                  <div className="text-[11px] text-gray-500 dark:text-gray-400">Superadmin</div>
                )}
              </div>
              <svg
                className={`h-4 w-4 text-gray-400 transition-transform ${menuOpen ? "rotate-180" : ""}`}
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </button>

            {menuOpen && (
              <div
                role="menu"
                className="absolute right-0 mt-2 w-48 overflow-hidden rounded-lg border border-gray-200 bg-white py-1 shadow-lg dark:border-gray-700 dark:bg-gray-800"
              >
                <button
                  role="menuitem"
                  onClick={() => { setMenuOpen(false); setProfileOpen(true); }}
                  className="flex w-full items-center gap-2.5 px-4 py-2 text-sm text-gray-700 transition-colors hover:bg-gray-100 dark:text-gray-200 dark:hover:bg-gray-700"
                >
                  <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  </svg>
                  {t("profile.title")}
                </button>
                <button
                  role="menuitem"
                  onClick={() => { setMenuOpen(false); logout(); }}
                  className="flex w-full items-center gap-2.5 px-4 py-2 text-sm text-red-600 transition-colors hover:bg-red-50 dark:text-red-400 dark:hover:bg-red-900/20"
                >
                  <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                  </svg>
                  {t("nav.logout")}
                </button>
              </div>
            )}
          </div>
        </div>
      </header>

      <ProfileModal open={profileOpen} onClose={() => setProfileOpen(false)} />
    </>
  );
}
