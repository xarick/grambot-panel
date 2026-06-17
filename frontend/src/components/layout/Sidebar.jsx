import { NavLink } from "react-router-dom";
import { useAuth } from "@/hooks/useAuth.jsx";
import { useTranslation } from "@/hooks/useTranslation.jsx";

const NAV_ITEMS = [
  {
    key: "nav.dashboard",
    to: "/dashboard",
    icon: (
      <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7h18M3 12h18M3 17h18" />
      </svg>
    ),
  },
  {
    key: "nav.bots",
    to: "/bots",
    icon: (
      <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.5 14.5L12 17m-7-5l16-7-3 16-5-4-3 3v-5l7-6" />
      </svg>
    ),
  },
  {
    key: "nav.broadcast",
    to: "/broadcast",
    icon: (
      <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5.882V19.24a1.76 1.76 0 01-3.417.592l-2.147-6.15M18 13a3 3 0 100-6M5.436 13.683A4.001 4.001 0 017 6h1.832c4.1 0 7.625-1.234 9.168-3v14c-1.543-1.766-5.067-3-9.168-3H7a3.988 3.988 0 01-1.564-.317z" />
      </svg>
    ),
  },
  {
    key: "nav.templates",
    to: "/templates",
    icon: (
      <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
      </svg>
    ),
  },
  {
    key: "nav.channels",
    to: "/channels",
    icon: (
      <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" />
      </svg>
    ),
  },
];

export function Sidebar() {
  const { user } = useAuth();
  const { t } = useTranslation();

  const navItems = user?.is_superuser
    ? [...NAV_ITEMS, {
        key: "nav.users",
        to: "/users",
        icon: (
          <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
        ),
      }]
    : NAV_ITEMS;

  return (
    <aside className="flex h-screen w-60 shrink-0 flex-col border-r border-gray-200 bg-white dark:border-gray-800 dark:bg-gray-900">
      <div className="flex h-14 items-center gap-2.5 border-b border-gray-200 px-5 dark:border-gray-800">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-600 text-sm font-bold text-white shadow-sm">
          TG
        </div>
        <span className="font-semibold tracking-tight text-gray-900 dark:text-gray-100">tg-panel</span>
      </div>

      <nav className="flex-1 space-y-1 overflow-y-auto px-3 py-4">
        {navItems.map((item) => (
          <NavLink
            key={item.key}
            to={item.to}
            className={({ isActive }) =>
              `relative flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors ${
                isActive
                  ? "bg-blue-50 font-medium text-blue-700 dark:bg-blue-900/30 dark:text-blue-400"
                  : "text-gray-600 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-800/70"
              }`
            }
          >
            {({ isActive }) => (
              <>
                {isActive && (
                  <span className="absolute left-0 top-1/2 h-5 w-1 -translate-y-1/2 rounded-r-full bg-blue-600 dark:bg-blue-500" />
                )}
                {item.icon}
                {t(item.key)}
              </>
            )}
          </NavLink>
        ))}
      </nav>

      <div className="border-t border-gray-200 px-5 py-3 dark:border-gray-800">
        <a
          href="https://itone.uz"
          target="_blank"
          rel="noopener noreferrer"
          className="group flex items-center justify-center gap-1 text-xs text-gray-400 transition-colors hover:text-blue-600 dark:text-gray-500 dark:hover:text-blue-400"
        >
          <span>Developed by</span>
          <span className="font-semibold text-gray-500 transition-colors group-hover:text-blue-600 dark:text-gray-300 dark:group-hover:text-blue-400">
            itone.uz
          </span>
        </a>
        <p className="mt-1 text-center text-[10px] tracking-wide text-gray-300 dark:text-gray-700">v1.0.0</p>
      </div>
    </aside>
  );
}
