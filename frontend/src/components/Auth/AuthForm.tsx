import { ReactNode } from "react";
import { Link } from "react-router-dom";

type AuthFormProps = {
  title: string;
  subtitle: string;
  footerLabel: string;
  footerLink: string;
  footerText: string;
  children: ReactNode;
  /** Optional Google Sign-In button rendered below the form with a divider. */
  googleButton?: ReactNode;
};

export const AuthFormLayout = ({
  title,
  subtitle,
  footerLabel,
  footerLink,
  footerText,
  children,
  googleButton,
}: AuthFormProps) => (
  <div className="flex min-h-screen items-center justify-center px-6 py-12">
    <div className="grid w-full max-w-5xl gap-8 lg:grid-cols-[1.2fr_0.8fr]">
      <section className="rounded-3xl border border-brand-200 bg-white/90 p-10 shadow-panel dark:border-brand-900/40 dark:bg-slate-800/90">
        <div className="mb-10 space-y-4">
          <p className="text-xs font-semibold uppercase tracking-[0.24em] text-brand-700 dark:text-brand-300">
            FairSight
          </p>
          <h1 className="text-3xl font-semibold text-slate-950 dark:text-white">{title}</h1>
          <p className="max-w-xl text-sm text-slate-600 dark:text-slate-300">{subtitle}</p>
        </div>
        {children}
        {googleButton && (
          <div className="mt-6">
            <div className="relative flex items-center gap-3">
              <div className="h-px flex-1 bg-slate-200 dark:bg-slate-700" />
              <span className="text-xs font-medium text-slate-400 dark:text-slate-500">or continue with</span>
              <div className="h-px flex-1 bg-slate-200 dark:bg-slate-700" />
            </div>
            <div className="mt-4 flex justify-center">{googleButton}</div>
          </div>
        )}
      </section>
      <aside className="panel hidden flex-col justify-between p-10 lg:flex">
        <div className="space-y-5">
          <span className="inline-flex rounded-full border border-brand-200 bg-brand-50 px-3 py-1 text-xs font-semibold text-brand-700 dark:border-brand-900/50 dark:bg-brand-950/40 dark:text-brand-200">
            Calm, actionable fairness review
          </span>
          <h2 className="text-2xl font-semibold text-slate-950 dark:text-white">
            See the bias before it sees you
          </h2>
          <p className="text-sm leading-6 text-slate-600 dark:text-slate-300">
            Upload a dataset, compare outcomes across protected groups, track intersectional harms,
            and export an immutable audit report for your stakeholders.
          </p>
        </div>
        <div className="space-y-3 rounded-2xl bg-slate-50 p-5 dark:bg-slate-900/70">
          <p className="font-medium text-slate-900 dark:text-white">{footerText}</p>
          <Link to={footerLink} className="text-sm font-semibold text-brand-700 dark:text-brand-300">
            {footerLabel}
          </Link>
        </div>
      </aside>
    </div>
  </div>
);

