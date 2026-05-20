"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { AppShell } from "@/components/app-shell";
import { Card, CardContent, CardTitle } from "@/components/ui/card";

export default function AdminPage() {
  const users = useQuery({ queryKey: ["admin-users"], queryFn: async () => (await api.get("/admin/users")).data });
  const audit = useQuery({ queryKey: ["audit"], queryFn: async () => (await api.get("/admin/audit-logs")).data });

  return (
    <AppShell>
      <div className="grid gap-6 xl:grid-cols-2">
        <Card>
          <CardTitle>User Management</CardTitle>
          <CardContent className="mt-4 space-y-3">
            {(users.data ?? []).map((u: any) => (
              <div key={u.id} className="rounded-2xl border border-white/10 bg-white/5 p-4 text-sm">
                <div className="font-medium">{u.full_name}</div>
                <div className="text-slate-400">{u.email} • {u.role}</div>
              </div>
            ))}
          </CardContent>
        </Card>
        <Card>
          <CardTitle>Audit Logs</CardTitle>
          <CardContent className="mt-4 space-y-3">
            {(audit.data ?? []).slice(0, 12).map((a: any) => (
              <div key={a.id} className="rounded-2xl border border-white/10 bg-white/5 p-4 text-sm">
                <div className="font-medium">{a.action}</div>
                <div className="text-slate-400">{a.entity_type} #{a.entity_id ?? "-"}</div>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    </AppShell>
  );
}
