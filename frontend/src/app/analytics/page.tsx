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
        <Card>
          <CardTitle>Insights</CardTitle>
          <CardContent className="mt-4 space-y-3 text-sm text-slate-300">
            <div>Total recognitions: {stats.data?.total_recognitions ?? 0}</div>
            <div>Unknown detections: {stats.data?.unknown_detections ?? 0}</div>
            <div>Average confidence: {stats.data?.avg_confidence ?? 0}</div>
          </CardContent>
        </Card>
      </div>
    </AppShell>
  );
}
