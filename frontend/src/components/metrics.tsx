"use client";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ArrowUpRight, ScanFace, Users, ShieldAlert, Activity } from "lucide-react";

export function MetricsGrid({ stats }: { stats: any }) {
  const items = [
    { label: "Registered Persons", value: stats?.total_persons ?? 0, icon: Users, extra: `${stats?.total_samples ?? 0} samples` },
    { label: "Recognitions", value: stats?.total_recognitions ?? 0, icon: ScanFace, extra: `${Math.round((stats?.recognition_rate ?? 0) * 100)}% hit rate` },
    { label: "Unknown Detections", value: stats?.unknown_detections ?? 0, icon: ShieldAlert, extra: `${stats?.recent_unknowns ?? 0} in 7 days` },
    { label: "Today Activity", value: stats?.today_recognitions ?? 0, icon: Activity, extra: `${stats?.active_users ?? 0} active users` },
  ];
  return (
    <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
      {items.map((it) => {
        const Icon = it.icon;
        return (
          <Card key={it.label}>
            <CardContent className="flex items-start justify-between p-0">
              <div>
                <div className="card-title">{it.label}</div>
                <div className="mt-2 text-3xl font-semibold">{it.value}</div>
                <div className="mt-2 text-xs text-slate-400">{it.extra}</div>
              </div>
              <div className="rounded-2xl bg-indigo-500/15 p-3 text-indigo-300">
                <Icon className="h-5 w-5" />
              </div>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}
