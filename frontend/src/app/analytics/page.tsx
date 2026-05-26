"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { AppShell } from "@/components/app-shell";
import { Card, CardContent, CardTitle } from "@/components/ui/card";
import { ActivityChart, ConfidenceChart, SourceChart } from "@/components/charts";

export default function AnalyticsPage() {
  const overview = useQuery({ queryKey: ["overview"], queryFn: async () => (await api.get("/analytics/overview")).data });
  const stats = useQuery({ queryKey: ["stats"], queryFn: async () => (await api.get("/dashboard/stats")).data });

  return (
    <AppShell>
      <div className="grid gap-6 xl:grid-cols-2">
        <ActivityChart data={stats.data?.daily_activity ?? []} />
        <ConfidenceChart data={overview.data?.confidence_buckets ?? []} />
        <SourceChart data={overview.data?.source_breakdown ?? []} />
        <Card className="glass-violet border-primary/20">
          <CardTitle className="text-white">Insights</CardTitle>
          <CardContent className="mt-4 space-y-3 text-sm text-slate-300">
            <div>Total recognitions: <span className="text-accent font-semibold">{stats.data?.total_recognitions ?? 0}</span></div>
            <div>Unknown detections: <span className="text-rose-300 font-semibold">{stats.data?.unknown_detections ?? 0}</span></div>
            <div>Average confidence: <span className="text-accent font-semibold">{stats.data?.avg_confidence ?? 0}</span></div>
          </CardContent>
        </Card>
      </div>
    </AppShell>
  );
}
