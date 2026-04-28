import { ReactElement } from "react";
import { Navigate } from "react-router-dom";

import { Skeleton } from "@/components/Common/Skeleton";
import { useAuth } from "@/hooks/useAuth";

export const ProtectedRoute = ({ children }: { children: ReactElement }) => {
  const { user, hydrated, isLoading } = useAuth();

  if (isLoading || !hydrated) {
    return (
      <div className="mx-auto flex min-h-screen max-w-7xl items-center justify-center px-6">
        <div className="w-full max-w-xl space-y-4">
          <Skeleton className="h-12 w-48" />
          <Skeleton className="h-40 w-full" />
        </div>
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  return children;
};
