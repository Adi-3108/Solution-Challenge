import { Component, ErrorInfo, ReactNode } from "react";

import { logger } from "@/utils/logger";

type ErrorBoundaryProps = {
  children: ReactNode;
};

type ErrorBoundaryState = {
  hasError: boolean;
};

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  state: ErrorBoundaryState = { hasError: false };

  static getDerivedStateFromError(): ErrorBoundaryState {
    return { hasError: true };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    logger.error("frontend_error_boundary", { error, errorInfo });
  }

  render(): ReactNode {
    if (this.state.hasError) {
      return (
        <div className="flex min-h-screen items-center justify-center px-6">
          <div className="panel max-w-lg space-y-4 p-8 text-center">
            <h1 className="text-2xl font-semibold text-slate-950 dark:text-white">
              FairSight ran into an unexpected problem
            </h1>
            <p className="text-sm text-slate-600 dark:text-slate-300">
              Reload the page and try again. If the problem persists, review the audit logs and server health checks.
            </p>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}

