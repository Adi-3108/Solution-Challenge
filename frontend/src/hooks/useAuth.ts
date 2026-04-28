import { useEffect } from "react";
import { useQuery } from "@tanstack/react-query";

import { authService } from "@/services/auth.service";
import { useAuthStore } from "@/stores/auth.store";

export const useAuth = () => {
  const { user, hydrated, setUser, setHydrated } = useAuthStore();
  const query = useQuery({
    queryKey: ["auth", "me"],
    queryFn: authService.me,
    retry: false,
  });

  useEffect(() => {
    if (query.isSuccess) {
      setUser(query.data);
      setHydrated(true);
      return;
    }
    if (query.isError) {
      setUser(null);
      setHydrated(true);
    }
  }, [query.data, query.isError, query.isSuccess, setHydrated, setUser]);

  return {
    user,
    hydrated,
    isLoading: query.isLoading && !hydrated,
  };
};

