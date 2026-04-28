import { LogOut, ShieldCheck } from "lucide-react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";

import { authService } from "@/services/auth.service";
import { useAuthStore } from "@/stores/auth.store";
import { ThemeToggle } from "@/components/Common/ThemeToggle";

const links = [
  { to: "/dashboard", label: "Dashboard" },
  { to: "/admin", label: "Admin" },
];

export const AppShell = () => {
  const navigate = useNavigate();
  const { user, reset } = useAuthStore();

  const handleLogout = async (): Promise<void> => {
    await authService.logout();
    reset();
    navigate("/login");
  };

  return (
    <div className="min-h-screen">
      <header className="sticky top-0 z-30 border-b border-slate-200/80 bg-white/80 backdrop-blur dark:border-slate-700 dark:bg-slate-900/80">
        <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-6 py-4">
          <div className="flex items-center gap-3">
            <div className="rounded-xl bg-brand-600 p-2 text-white">
              <ShieldCheck className="h-5 w-5" />
            </div>
            <div>
              <p className="font-semibold text-slate-950 dark:text-white">FairSight</p>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                See the bias before it sees you
              </p>
            </div>
          </div>
          <nav className="hidden items-center gap-2 md:flex">
            {links
              .filter((link) => user?.role === "admin" || link.to !== "/admin")
              .map((link) => (
                <NavLink
                  key={link.to}
                  to={link.to}
                  className={({ isActive }) =>
                    isActive
                      ? "button-primary"
                      : "button-secondary border-transparent bg-transparent"
                  }
                >
                  {link.label}
                </NavLink>
              ))}
          </nav>
          <div className="flex items-center gap-3">
            <ThemeToggle />
            <div className="hidden text-right md:block">
              <p className="font-medium text-slate-900 dark:text-white">{user?.email}</p>
              <p className="text-xs uppercase tracking-wide text-slate-500 dark:text-slate-400">
                {user?.role}
              </p>
            </div>
            <button
              type="button"
              onClick={handleLogout}
              className="button-secondary gap-2"
              aria-label="Log out"
            >
              <LogOut className="h-4 w-4" />
              Logout
            </button>
          </div>
        </div>
      </header>
      <main className="mx-auto max-w-7xl px-6 py-8">
        <Outlet />
      </main>
    </div>
  );
};

