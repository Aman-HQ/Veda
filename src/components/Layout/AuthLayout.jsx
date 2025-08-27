export default function AuthLayout({ children }) {
  return (
    <div className="min-h-screen w-full flex items-center justify-center bg-gradient-to-b from-indigo-50 via-white to-white dark:from-slate-900 dark:via-slate-950 dark:to-black px-4 sm:px-4">
      <div className="w-full max-w-md mx-auto">{children}</div>
    </div>
  );
}


