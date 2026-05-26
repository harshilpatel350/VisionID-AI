"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { AppShell } from "@/components/app-shell";
import { MetricsGrid } from "@/components/metrics";
import { ActivityChart, ConfidenceChart, SourceChart } from "@/components/charts";
import { Card, CardContent, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import Link from "next/link";
import { WebcamModal } from "@/components/webcam-modal";
import { formatDate } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { useState } from "react";
import { motion } from "framer-motion";

export default function DashboardPage() {
  const stats = useQuery({ queryKey: ["stats"], queryFn: async () => (await api.get("/dashboard/stats")).data });
  const overview = useQuery({ queryKey: ["overview"], queryFn: async () => (await api.get("/analytics/overview")).data });
  const persons = useQuery({ queryKey: ["persons"], queryFn: async () => (await api.get("/faces/persons")).data });

  return (
    <AppShell>
      <div className="space-y-6">
        <motion.section 
          initial={{ opacity: 0, y: -20 }} 
          animate={{ opacity: 1, y: 0 }} 
          transition={{ duration: 0.5 }}
          className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between"
        >
          <div>
            <h1 className="text-3xl font-bold tracking-tight text-white">VisionID Intelligence</h1>
            <p className="mt-2 max-w-2xl text-sm text-muted">High-performance face registry, real-time recognition, and analytics console.</p>
          </div>
          <div className="flex flex-wrap gap-3">
            <WebcamModal />
            <Link href="/registry"><Button variant="outline" className="border-primary/20 text-accent hover:bg-primary/10">Add registry entry</Button></Link>
          </div>
        </motion.section>

        <MetricsGrid stats={stats.data} />

        <div className="grid gap-6 xl:grid-cols-2">
          <ActivityChart data={stats.data?.daily_activity ?? []} />
          <ConfidenceChart data={overview.data?.confidence_buckets ?? []} />
          <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} transition={{ duration: 0.4, delay: 0.3 }}>
            <Card className="h-full glass-violet border-primary/20">
              <CardTitle className="text-white">Recent Recognition Trends</CardTitle>
              <CardContent className="mt-4 space-y-3">
                {(stats.data?.top_persons ?? []).map((item: any) => (
                  <div key={item.name} className="flex items-center justify-between rounded-2xl border border-white/5 bg-black/20 px-4 py-3 hover:bg-primary/10 transition-colors">
                    <div>
                      <div className="font-medium text-white">{item.name}</div>
                      <div className="text-xs text-muted">Top recognized identity</div>
                    </div>
                    <Badge className="bg-primary/20 text-accent hover:bg-primary/30 border-none">{item.hits} hits</Badge>
                  </div>
                ))}
              </CardContent>
            </Card>
          </motion.div>
        </div>

        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, delay: 0.4 }}>
          <Card className="glass-violet border-primary/20">
            <CardTitle className="text-white">Registered Persons</CardTitle>
            <CardContent className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-3">
              {(persons.data ?? []).slice(0, 6).map((p: any) => (
                <div key={p.id} className="rounded-2xl border border-white/5 bg-black/20 p-4 hover:border-primary/30 hover:bg-primary/5 transition-all">
                  <div className="text-base font-semibold text-white">{p.full_name}</div>
                  <div className="mt-1 text-xs text-muted">{p.person_code}</div>
                  <div className="mt-3 text-sm text-slate-300">{p.department ?? "No department"}</div>
                  <div className="mt-4 text-xs text-primary">{p.sample_count} samples • {formatDate(p.created_at)}</div>
                </div>
              ))}
            </CardContent>
          </Card>
        </motion.div>
      </div>
    </AppShell>
  );
}
