export function Input({ label, error, className = "", ...props }) {
  return (
    <div className="flex flex-col gap-1">
      {label && (
        <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
          {label}
        </label>
      )}
      <input
        className={`w-full px-3 py-2 rounded-lg border text-sm bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100
          border-gray-300 dark:border-gray-600 placeholder-gray-400 dark:placeholder-gray-500
          focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent
          disabled:opacity-50 disabled:cursor-not-allowed ${error ? "border-red-500" : ""} ${className}`}
        {...props}
      />
      {error && <p className="text-xs text-red-500">{error}</p>}
    </div>
  );
}

export function Textarea({ label, error, className = "", ...props }) {
  return (
    <div className="flex flex-col gap-1">
      {label && (
        <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
          {label}
        </label>
      )}
      <textarea
        className={`w-full px-3 py-2 rounded-lg border text-sm bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100
          border-gray-300 dark:border-gray-600 placeholder-gray-400 dark:placeholder-gray-500
          focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent
          resize-none disabled:opacity-50 ${error ? "border-red-500" : ""} ${className}`}
        {...props}
      />
      {error && <p className="text-xs text-red-500">{error}</p>}
    </div>
  );
}

export function Select({ label, error, children, className = "", ...props }) {
  return (
    <div className="flex flex-col gap-1">
      {label && (
        <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
          {label}
        </label>
      )}
      <select
        className={`w-full px-3 py-2 rounded-lg border text-sm bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100
          border-gray-300 dark:border-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500
          focus:border-transparent disabled:opacity-50 ${error ? "border-red-500" : ""} ${className}`}
        {...props}
      >
        {children}
      </select>
      {error && <p className="text-xs text-red-500">{error}</p>}
    </div>
  );
}
