import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { Card } from "@/components/Common/Card";
import { PageHeader } from "@/components/Common/PageHeader";
import { adminService } from "@/services/admin.service";
import { useAuthStore } from "@/stores/auth.store";
import { formatDate } from "@/utils/format";

export const AdminPage = () => {
  const queryClient = useQueryClient();
  const { user } = useAuthStore();
  const usersQuery = useQuery({
    queryKey: ["admin-users"],
    queryFn: adminService.users,
    enabled: user?.role === "admin",
  });
  const auditLogQuery = useQuery({
    queryKey: ["audit-log"],
    queryFn: adminService.auditLog,
    enabled: user?.role === "admin",
  });
  const updateUserMutation = useMutation({
    mutationFn: ({ userId, role }: { userId: string; role: "admin" | "analyst" | "viewer" }) =>
      adminService.updateUserRole(userId, role),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["admin-users"] }),
  });

  if (user?.role !== "admin") {
    return (
      <Card>
        <p className="text-sm text-slate-600 dark:text-slate-300">
          Admin access is required to view users and the full audit trail.
        </p>
      </Card>
    );
  }

  return (
    <div className="space-y-8">
      <PageHeader
        title="Admin controls"
        subtitle="Review all user accounts, inspect platform-level audit logs, and verify access governance."
      />
      <section className="grid gap-6 xl:grid-cols-[0.9fr_1.1fr]">
        <Card className="space-y-4 overflow-x-auto">
          <h2 className="text-lg font-semibold text-slate-950 dark:text-white">Users</h2>
          <table className="min-w-full text-left text-sm">
            <thead className="sticky top-0 bg-white dark:bg-slate-800">
              <tr className="text-slate-500 dark:text-slate-400">
                <th className="px-3 py-2">Email</th>
                <th className="px-3 py-2">Role</th>
                <th className="px-3 py-2">Created</th>
              </tr>
            </thead>
            <tbody>
              {usersQuery.data?.map((record) => (
                <tr key={record.id} className="border-t border-slate-200 dark:border-slate-700">
                  <td className="px-3 py-3 text-slate-900 dark:text-white">{record.email}</td>
                  <td className="px-3 py-3">
                    <select
                      value={record.role}
                      className="button-secondary"
                      onChange={(event) =>
                        updateUserMutation.mutate({
                          userId: record.id,
                          role: event.target.value as "admin" | "analyst" | "viewer",
                        })
                      }
                    >
                      <option value="admin">Admin</option>
                      <option value="analyst">Analyst</option>
                      <option value="viewer">Viewer</option>
                    </select>
                  </td>
                  <td className="px-3 py-3 text-slate-600 dark:text-slate-300">
                    {formatDate(record.created_at)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>

        <Card className="space-y-4 overflow-x-auto">
          <h2 className="text-lg font-semibold text-slate-950 dark:text-white">Audit log</h2>
          <table className="min-w-full text-left text-sm">
            <thead className="sticky top-0 bg-white dark:bg-slate-800">
              <tr className="text-slate-500 dark:text-slate-400">
                <th className="px-3 py-2">Action</th>
                <th className="px-3 py-2">Resource</th>
                <th className="px-3 py-2">When</th>
              </tr>
            </thead>
            <tbody>
              {auditLogQuery.data?.map((record) => (
                <tr key={record.id} className="border-t border-slate-200 dark:border-slate-700">
                  <td className="px-3 py-3 text-slate-900 dark:text-white">{record.action}</td>
                  <td className="px-3 py-3 text-slate-600 dark:text-slate-300">
                    {record.resource_type} | {record.resource_id}
                  </td>
                  <td className="px-3 py-3 text-slate-600 dark:text-slate-300">
                    {formatDate(record.created_at)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      </section>
    </div>
  );
};
