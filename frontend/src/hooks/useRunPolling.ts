import { useQuery } from "@tanstack/react-query";

import { runsService } from "@/services/runs.service";

export const useRunPolling = (runId: string) =>
  useQuery({
    queryKey: ["runs", runId],
    queryFn: () => runsService.detail(runId),
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      if (status === "completed" || status === "failed") {
        return false;
      }
      return 3000;
    },
  });

