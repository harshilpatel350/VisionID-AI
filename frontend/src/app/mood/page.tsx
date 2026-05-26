"use client";

import { useEffect, useState } from "react";
import { AppShell } from "@/components/app-shell";
import { Card } from "@/components/ui/card";
import { api } from "@/lib/api";
import { Smile, Frown, Meh, AlertCircle, HelpCircle } from "lucide-react";

export default function MoodAnalyticsPage() {
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const res = await api.get("/mood/stats");
        setStats(res.data);
      } catch (err) {
        console.error("Failed to fetch mood stats", err);
      } finally {
        setLoading(false);
      }
    };
    fetchStats();
  }, []);

  const moodIcons: Record<string, any> = {
    happy: { icon: Smile, color: "text-green-500", bg: "bg-green-500/10" },
    sad: { icon: Frown, color: "text-blue-500", bg: "bg-blue-500/10" },
    angry: { icon: AlertCircle, color: "text-red-500", bg: "bg-red-500/10" },
    surprise: { icon: HelpCircle, color: "text-yellow-500", bg: "bg-yellow-500/10" },
    neutral: { icon: Meh, color: "text-gray-500", bg: "bg-gray-500/10" },
    fear: { icon: Frown, color: "text-purple-500", bg: "bg-purple-500/10" },
    disgust: { icon: AlertCircle, color: "text-orange-500", bg: "bg-orange-500/10" },
  };

  return (
    <AppShell>
      <div className="flex flex-col mb-6">
        <h1 className="text-3xl font-bold tracking-tight text-white mb-1">Emotion Analytics</h1>
        <p className="text-muted">Aggregate mood analysis across all tracked individuals.</p>
      </div>

      {loading ? (
        <div className="flex justify-center p-12">
          <div className="w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin"></div>
        </div>
      ) : stats ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card className="p-6 col-span-full md:col-span-1 lg:col-span-1 glass-violet border-primary/20 flex flex-col justify-center items-center text-center">
            <h3 className="text-xs font-semibold text-accent uppercase tracking-wider mb-2">Total Scans</h3>
            <div className="text-5xl font-bold text-white mb-2 shadow-glow-violet">{stats.total_records}</div>
            <p className="text-xs text-muted">Emotional data points collected</p>
          </Card>
          
          <div className="col-span-full md:col-span-1 lg:col-span-3 grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {Object.entries(stats.mood_distribution).sort((a: any, b: any) => b[1] - a[1]).map(([mood, count]: [string, any]) => {
              const conf = moodIcons[mood.toLowerCase()] || moodIcons.neutral;
              const Icon = conf.icon;
              const percentage = stats.total_records > 0 ? (count / stats.total_records * 100).toFixed(1) : 0;
              
              return (
                <Card key={mood} className="p-4 glass-violet border-primary/20 hover:border-primary/40 hover:shadow-glow-violet transition-all duration-300">
                  <div className="flex items-center gap-3 mb-3">
                    <div className={`p-2 rounded-lg ${conf.bg} ${conf.color}`}>
                      <Icon size={20} />
                    </div>
                    <span className="font-semibold text-white capitalize">{mood}</span>
                  </div>
                  <div className="flex items-end justify-between">
                    <span className="text-2xl font-bold text-white">{count}</span>
                    <span className="text-sm text-muted">{percentage}%</span>
                  </div>
                  <div className="w-full bg-black/35 h-1.5 rounded-full mt-3 overflow-hidden">
                    <div 
                      className={`h-full ${conf.bg.replace('/10', '')}`} 
                      style={{ width: `${percentage}%` }}
                    />
                  </div>
                </Card>
              );
            })}
          </div>
        </div>
      ) : (
        <Card className="p-12 text-center text-muted border-dashed border-primary/20 glass-violet">
          No mood data available yet.
        </Card>
      )}
    </AppShell>
  );
}
