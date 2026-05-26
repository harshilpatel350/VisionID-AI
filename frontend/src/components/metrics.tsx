"use client";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ArrowUpRight, ScanFace, Users, ShieldAlert, Activity } from "lucide-react";
import { motion, useSpring, useTransform } from "framer-motion";
import { useEffect } from "react";

function AnimatedNumber({ value }: { value: number }) {
  const spring = useSpring(0, { bounce: 0, duration: 1200 });
  const display = useTransform(spring, (current) => Math.round(current).toLocaleString());

  useEffect(() => {
    spring.set(value);
  }, [spring, value]);

  return <motion.span>{display}</motion.span>;
}

export function MetricsGrid({ stats }: { stats: any }) {
  const items = [
    { label: "Registered Persons", value: stats?.total_persons ?? 0, icon: Users, extra: `${stats?.total_samples ?? 0} samples` },
    { label: "Recognitions", value: stats?.total_recognitions ?? 0, icon: ScanFace, extra: `${Math.round((stats?.recognition_rate ?? 0) * 100)}% hit rate` },
    { label: "Unknown Detections", value: stats?.unknown_detections ?? 0, icon: ShieldAlert, extra: `${stats?.recent_unknowns ?? 0} in 7 days` },
    { label: "Today Activity", value: stats?.today_recognitions ?? 0, icon: Activity, extra: `${stats?.active_users ?? 0} active users` },
  ];
  return (
    <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
      {items.map((it, idx) => {
        const Icon = it.icon;
        return (
          <motion.div
            key={it.label}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: idx * 0.1 }}
          >
            <Card className="h-full glass-violet border-primary/20 hover:border-primary/40 transition-colors">
              <CardContent className="flex items-start justify-between p-0 h-full">
                <div>
                  <div className="card-title text-white">{it.label}</div>
                  <div className="mt-2 text-3xl font-bold tracking-tight text-white">
                    <AnimatedNumber value={it.value} />
                  </div>
                  <div className="mt-2 text-xs text-muted">{it.extra}</div>
                </div>
                <div className="rounded-2xl bg-primary/20 p-3 text-accent shadow-glow-violet">
                  <Icon className="h-5 w-5" />
                </div>
              </CardContent>
            </Card>
          </motion.div>
        );
      })}
    </div>
  );
}
