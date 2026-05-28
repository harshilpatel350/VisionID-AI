"use client";

import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { API_BASE, api } from "@/lib/api";
import { AppShell } from "@/components/app-shell";
import { Card, CardContent, CardTitle } from "@/components/ui/card";
import { ActivityChart, ConfidenceChart, FacesPerHourChart, MoodDistributionChart, SourceChart } from "@/components/charts";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { formatDate } from "@/lib/utils";
import { Dialog, DialogContent, DialogTitle } from "@/components/ui/dialog";

export default function AnalyticsPage() {
  const overview = useQuery({ queryKey: ["overview"], queryFn: async () => (await api.get("/analytics/overview")).data });
  const stats = useQuery({ queryKey: ["stats"], queryFn: async () => (await api.get("/dashboard/stats")).data });
  const [filters, setFilters] = useState({
    start: "",
    end: "",
    mood: "",
    status: "all",
    name: "",
    sort: "desc",
  });
  const [activeFilters, setActiveFilters] = useState(filters);
  const [page, setPage] = useState(1);
  const pageSize = 50;
  const [selectedLog, setSelectedLog] = useState<any | null>(null);
  const [detailOpen, setDetailOpen] = useState(false);

  const logs = useQuery({
    queryKey: ["logs", activeFilters, page],
    queryFn: async () => {
      const params: any = { page, page_size: pageSize };
      if (activeFilters.start) params.start = activeFilters.start;
      if (activeFilters.end) params.end = activeFilters.end;
      if (activeFilters.mood) params.mood = activeFilters.mood;
      if (activeFilters.status === "known") params.is_unknown = false;
      if (activeFilters.status === "unknown") params.is_unknown = true;
      if (activeFilters.name) params.person_name = activeFilters.name;
      if (activeFilters.sort) params.sort = activeFilters.sort;
      const res = await api.get("/recognition/logs", { params });
      const items = Array.isArray(res.data) ? res.data : (res.data?.value ?? []);
      const meta = (res.data as any)?._meta;
      return { items, meta };
    },
  });

  const hasNextPage = Boolean(logs.data?.meta?.has_more);
  const totalPages = logs.data?.meta ? Math.ceil(logs.data.meta.total / logs.data.meta.page_size) : undefined;

  const exportCsv = async () => {
    const params: any = {};
    if (activeFilters.start) params.start = activeFilters.start;
    if (activeFilters.end) params.end = activeFilters.end;
    if (activeFilters.mood) params.mood = activeFilters.mood;
    if (activeFilters.status === "known") params.is_unknown = false;
    if (activeFilters.status === "unknown") params.is_unknown = true;
    if (activeFilters.name) params.person_name = activeFilters.name;
    if (activeFilters.sort) params.sort = activeFilters.sort;

    const res = await api.get("/exports/recognition.csv", { params, responseType: "blob" });
    const blob = new Blob([res.data], { type: "text/csv" });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement("a");
    const stamp = new Date().toISOString().slice(0, 10);
    link.href = url;
    link.download = `recognition_logs_${stamp}.csv`;
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  };

  const exportXlsx = async () => {
    const params: any = {};
    if (activeFilters.start) params.start = activeFilters.start;
    if (activeFilters.end) params.end = activeFilters.end;
    if (activeFilters.mood) params.mood = activeFilters.mood;
    if (activeFilters.status === "known") params.is_unknown = false;
    if (activeFilters.status === "unknown") params.is_unknown = true;
    if (activeFilters.name) params.person_name = activeFilters.name;
    if (activeFilters.sort) params.sort = activeFilters.sort;

    const res = await api.get("/exports/recognition.xlsx", { params, responseType: "blob" });
    const blob = new Blob([res.data], { type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement("a");
    const stamp = new Date().toISOString().slice(0, 10);
    link.href = url;
    link.download = `recognition_logs_${stamp}.xlsx`;
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  };

  const exportFromDetail = async (format: "csv" | "xlsx") => {
    if (!selectedLog) return;
    const params: any = { page: 1, page_size: pageSize };
    if (selectedLog.occurred_at) {
      params.start = selectedLog.occurred_at;
      params.end = selectedLog.occurred_at;
    }
    if (selectedLog.person_name && !selectedLog.is_unknown) params.person_name = selectedLog.person_name;
    if (selectedLog.mood) params.mood = selectedLog.mood;
    params.is_unknown = selectedLog.is_unknown;
    params.sort = "desc";

    const endpoint = format === "csv" ? "/exports/recognition.csv" : "/exports/recognition.xlsx";
    const res = await api.get(endpoint, { params, responseType: "blob" });
    const mime = format === "csv" ? "text/csv" : "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet";
    const blob = new Blob([res.data], { type: mime });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement("a");
    const stamp = new Date().toISOString().slice(0, 10);
    link.href = url;
    link.download = `recognition_log_${stamp}.${format}`;
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  };

  const toLocalInputValue = (date: Date) => {
    const local = new Date(date.getTime() - date.getTimezoneOffset() * 60000);
    return local.toISOString().slice(0, 16);
  };

  const quickRange = (hours: number) => {
    const end = new Date();
    const start = new Date(end.getTime() - hours * 60 * 60 * 1000);
    const next = { ...filters, start: toLocalInputValue(start), end: toLocalInputValue(end) };
    setFilters(next);
    setActiveFilters(next);
    setPage(1);
  };

  const openDetail = (log: any) => {
    setSelectedLog(log);
    setDetailOpen(true);
  };

  const moodData = useMemo(() => {
    const dist = overview.data?.mood_distribution ?? {};
    return Object.entries(dist).map(([mood, count]) => ({ mood, count }));
  }, [overview.data]);

  const facesPerHour = overview.data?.faces_per_hour ?? [];
  const topPersons = overview.data?.top_persons ?? stats.data?.top_persons ?? [];

  return (
    <AppShell>
      <div className="space-y-6">
        <div className="grid gap-6 xl:grid-cols-2">
          <ActivityChart data={stats.data?.daily_activity ?? []} />
          <FacesPerHourChart data={facesPerHour} />
          <ConfidenceChart data={overview.data?.confidence_buckets ?? []} />
          <SourceChart data={overview.data?.source_breakdown ?? []} />
          <MoodDistributionChart data={moodData} />
          <Card className="glass-violet border-primary/20">
            <CardTitle className="text-white">Top Repeated Persons</CardTitle>
            <CardContent className="mt-4 space-y-3 text-sm text-slate-300">
              {topPersons.length ? topPersons.map((p: any) => (
                <div key={p.name} className="flex items-center justify-between rounded-2xl border border-white/5 bg-black/20 px-4 py-3">
                  <div className="text-white font-medium">{p.name}</div>
                  <Badge className="bg-primary/20 text-accent border-none">{p.hits} hits</Badge>
                </div>
              )) : (
                <div className="text-muted">No recognition activity yet.</div>
              )}
            </CardContent>
          </Card>
        </div>

        <Card className="glass-violet border-primary/20">
          <CardTitle className="text-white">Recognition Timeline</CardTitle>
          <CardContent className="mt-4 space-y-4">
            <div className="flex flex-wrap gap-2">
              <Button variant="secondary" className="bg-primary/10 text-accent border border-primary/20" onClick={() => quickRange(24)}>
                Last 24h
              </Button>
              <Button variant="secondary" className="bg-primary/10 text-accent border border-primary/20" onClick={() => quickRange(24 * 7)}>
                Last 7d
              </Button>
              <Button variant="secondary" className="bg-primary/10 text-accent border border-primary/20" onClick={() => quickRange(24 * 30)}>
                Last 30d
              </Button>
            </div>
            <div className="grid gap-3 md:grid-cols-[1.2fr_1fr_1fr_1fr_1fr_1fr_auto_auto]">
              <Input
                type="text"
                placeholder="Search name"
                value={filters.name}
                onChange={(e) => setFilters({ ...filters, name: e.target.value })}
                className="bg-black/20 border-white/10"
              />
              <Input
                type="datetime-local"
                value={filters.start}
                onChange={(e) => setFilters({ ...filters, start: e.target.value })}
                className="bg-black/20 border-white/10"
              />
              <Input
                type="datetime-local"
                value={filters.end}
                onChange={(e) => setFilters({ ...filters, end: e.target.value })}
                className="bg-black/20 border-white/10"
              />
              <select
                className="h-11 rounded-xl border border-white/10 bg-black/20 px-3 text-sm text-white"
                value={filters.mood}
                onChange={(e) => setFilters({ ...filters, mood: e.target.value })}
              >
                <option value="">All moods</option>
                {Object.keys(overview.data?.mood_distribution ?? {}).map((m) => (
                  <option key={m} value={m}>{m}</option>
                ))}
              </select>
              <select
                className="h-11 rounded-xl border border-white/10 bg-black/20 px-3 text-sm text-white"
                value={filters.status}
                onChange={(e) => setFilters({ ...filters, status: e.target.value })}
              >
                <option value="all">All</option>
                <option value="known">Known</option>
                <option value="unknown">Unknown</option>
              </select>
              <select
                className="h-11 rounded-xl border border-white/10 bg-black/20 px-3 text-sm text-white"
                value={filters.sort}
                onChange={(e) => setFilters({ ...filters, sort: e.target.value })}
              >
                <option value="desc">Newest first</option>
                <option value="asc">Oldest first</option>
              </select>
              <div className="flex gap-2">
                <Button
                  variant="secondary"
                  className="bg-primary/20 text-accent border border-primary/30"
                  onClick={() => {
                    setActiveFilters(filters);
                    setPage(1);
                  }}
                >
                  Apply
                </Button>
                <Button
                  variant="ghost"
                  onClick={() => {
                    const reset = { start: "", end: "", mood: "", status: "all", name: "", sort: "desc" };
                    setFilters(reset);
                    setActiveFilters(reset);
                    setPage(1);
                  }}
                >
                  Reset
                </Button>
              </div>
              <div className="flex">
                <div className="flex gap-2">
                  <Button variant="outline" className="border-primary/20 text-accent" onClick={exportCsv}>
                    Export CSV
                  </Button>
                  <Button variant="outline" className="border-primary/20 text-accent" onClick={exportXlsx}>
                    Export XLSX
                  </Button>
                </div>
              </div>
            </div>

            <div className="space-y-3">
              {logs.isLoading ? (
                <div className="text-sm text-muted">Loading logs...</div>
              ) : logs.data?.items?.length ? (
                logs.data.items.map((log: any) => (
                  <div key={log.id} className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-white/5 bg-black/20 px-4 py-3">
                    <div>
                      <div className="text-white font-medium">
                        {log.is_unknown ? "Unknown" : log.person_name || "Unknown"}
                      </div>
                      <div className="text-xs text-muted">{formatDate(log.occurred_at)} · {log.source_type}</div>
                    </div>
                    <div className="flex flex-wrap items-center gap-2 text-xs">
                      <Badge className={log.is_unknown ? "bg-rose-500/20 text-rose-300 border-none" : "bg-emerald-500/20 text-emerald-300 border-none"}>
                        {log.is_unknown ? "UNKNOWN" : "KNOWN"}
                      </Badge>
                      {log.mood && <Badge className="bg-primary/20 text-accent border-none">{log.mood}</Badge>}
                      <Badge className="bg-white/10 text-slate-200 border-none">{Math.round((log.confidence ?? 0) * 100)}%</Badge>
                      <Button variant="ghost" size="sm" onClick={() => openDetail(log)}>
                        Details
                      </Button>
                    </div>
                  </div>
                ))
              ) : (
                <div className="text-sm text-muted">No logs match your filters.</div>
              )}
            </div>
            <div className="flex items-center justify-between pt-2">
              <Button
                variant="ghost"
                disabled={page <= 1}
                onClick={() => setPage((p) => Math.max(1, p - 1))}
              >
                Previous
              </Button>
              <div className="text-xs text-muted">Page {page}{totalPages ? ` of ${totalPages}` : ""}</div>
              <Button
                variant="ghost"
                disabled={!hasNextPage}
                onClick={() => setPage((p) => p + 1)}
              >
                Next
              </Button>
            </div>
          </CardContent>
        </Card>

        <Card className="glass-violet border-primary/20">
          <CardTitle className="text-white">Insights</CardTitle>
          <CardContent className="mt-4 space-y-3 text-sm text-slate-300">
            <div>Total recognitions: <span className="text-accent font-semibold">{stats.data?.total_recognitions ?? 0}</span></div>
            <div>Unknown detections: <span className="text-rose-300 font-semibold">{stats.data?.unknown_detections ?? 0}</span></div>
            <div>Average confidence: <span className="text-accent font-semibold">{stats.data?.avg_confidence ?? 0}</span></div>
          </CardContent>
        </Card>
      </div>
      <Dialog open={detailOpen} onOpenChange={setDetailOpen}>
        <DialogContent className="max-w-3xl bg-[rgb(var(--panel))]/95 border-primary/20">
          <DialogTitle className="text-white">Recognition Details</DialogTitle>
          {selectedLog && (
            <div className="mt-4 grid gap-4 md:grid-cols-[220px_1fr]">
              <div className="rounded-2xl border border-white/10 bg-black/30 p-3">
                <div className="text-xs text-muted mb-2">Snapshot</div>
                {selectedLog.snapshot_path ? (
                  <img src={`${API_BASE}/${selectedLog.snapshot_path}`} alt="Snapshot" className="w-full rounded-xl object-cover" />
                ) : (
                  <div className="h-40 rounded-xl border border-dashed border-white/10 flex items-center justify-center text-xs text-muted">No snapshot</div>
                )}
              </div>
              <div className="space-y-3">
                <div className="text-lg font-semibold text-white">
                  {selectedLog.is_unknown ? "Unknown" : selectedLog.person_name || "Unknown"}
                </div>
                <div className="text-xs text-muted">{formatDate(selectedLog.occurred_at)} · {selectedLog.source_type}</div>
                <div className="flex flex-wrap gap-2 text-xs">
                  <Badge className={selectedLog.is_unknown ? "bg-rose-500/20 text-rose-300 border-none" : "bg-emerald-500/20 text-emerald-300 border-none"}>
                    {selectedLog.is_unknown ? "UNKNOWN" : "KNOWN"}
                  </Badge>
                  {selectedLog.mood && <Badge className="bg-primary/20 text-accent border-none">{selectedLog.mood}</Badge>}
                  <Badge className="bg-white/10 text-slate-200 border-none">{Math.round((selectedLog.confidence ?? 0) * 100)}%</Badge>
                  <Button variant="outline" size="sm" className="border-primary/20 text-accent" onClick={() => exportFromDetail("csv")}>Export CSV</Button>
                  <Button variant="outline" size="sm" className="border-primary/20 text-accent" onClick={() => exportFromDetail("xlsx")}>Export XLSX</Button>
                </div>

                <div className="grid gap-2 md:grid-cols-2 text-xs text-slate-200">
                  <div className="rounded-xl border border-white/10 bg-black/30 px-3 py-2">Liveness: {selectedLog.liveness_score != null ? `${Math.round(selectedLog.liveness_score * 100)}%` : "-"}</div>
                  <div className="rounded-xl border border-white/10 bg-black/30 px-3 py-2">Enhanced: {selectedLog.is_enhanced ? "Yes" : "No"}</div>
                  <div className="rounded-xl border border-white/10 bg-black/30 px-3 py-2">Quality: {selectedLog.quality_score != null ? `${Math.round(selectedLog.quality_score * 100)}%` : "-"}</div>
                  <div className="rounded-xl border border-white/10 bg-black/30 px-3 py-2">Pose: {selectedLog.pose_score != null ? `${Math.round(selectedLog.pose_score * 100)}%` : "-"}</div>
                  <div className="rounded-xl border border-white/10 bg-black/30 px-3 py-2">Low-light: {selectedLog.low_light_score != null ? `${Math.round(selectedLog.low_light_score * 100)}%` : "-"}</div>
                  <div className="rounded-xl border border-white/10 bg-black/30 px-3 py-2">Size: {selectedLog.size_score != null ? `${Math.round(selectedLog.size_score * 100)}%` : "-"}</div>
                </div>

                <div className="grid gap-2 md:grid-cols-2 text-xs">
                  <div className="rounded-xl border border-white/10 bg-black/30 p-3">
                    <div className="text-muted mb-1">Bounding Box</div>
                    <pre className="text-[11px] text-slate-200 whitespace-pre-wrap">{JSON.stringify(selectedLog.bounding_box_json, null, 2)}</pre>
                  </div>
                  <div className="rounded-xl border border-white/10 bg-black/30 p-3">
                    <div className="text-muted mb-1">Mood Scores</div>
                    <pre className="text-[11px] text-slate-200 whitespace-pre-wrap">{JSON.stringify(selectedLog.mood_scores_json ?? {}, null, 2)}</pre>
                  </div>
                </div>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </AppShell>
  );
}
