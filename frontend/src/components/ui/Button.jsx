export function Button({ children, variant = "primary", size = "md", className = "", ...props }) {
  const base = "inline-flex items-center justify-center font-medium rounded-lg transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed";

  const variants = {
    primary: "bg-blue-600 text-white hover:bg-blue-700 focus-visible:ring-blue-500 dark:bg-blue-500 dark:hover:bg-blue-600",
    secondary: "bg-gray-100 text-gray-700 hover:bg-gray-200 focus-visible:ring-gray-400 dark:bg-gray-700 dark:text-gray-200 dark:hover:bg-gray-600",
    danger: "bg-red-600 text-white hover:bg-red-700 focus-visible:ring-red-500",
    ghost: "text-gray-600 hover:bg-gray-100 focus-visible:ring-gray-400 dark:text-gray-400 dark:hover:bg-gray-700",
  };

  const sizes = {
    sm: "px-3 py-1.5 text-sm gap-1.5",
    md: "px-4 py-2 text-sm gap-2",
    lg: "px-5 py-2.5 text-base gap-2",
  };

  return (
    <button className={`${base} ${variants[variant]} ${sizes[size]} ${className}`} {...props}>
      {children}
    </button>
  );
}
