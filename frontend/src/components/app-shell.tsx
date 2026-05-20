"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { motion } from "framer-motion";
import {
  LayoutDashboard, ScanFace, Search, MonitorUp, ChartColumn, Settings, ShieldCheck, LogOut, Menu, Sparkles
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { clearAuth, getStoredUser } from "@/lib/auth";
import { useEffect, useState } from "react";
import { cn } from "@/lib/utils";

const nav = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/registry", label: "Registry", icon: ScanFace },
  { href: "/studio", label: "Studio", icon: Sparkles },
  { href: "/live", label: "Live Webcam", icon: MonitorUp },
  { href: "/search", label: "Search", icon: Search },
  { href: "/analytics", label: "Analytics", icon: ChartColumn },
  { href: "/admin", label: "Admin", icon: ShieldCheck },
  { href: "/settings", label: "Settings", icon: Settings },
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const path = usePathname();
  const router = useRouter();
  const [open, setOpen] = useState(true);
  const [user, setUser] = useState<{ full_name: string; role: string } | null>(null);

  useEffect(() => {
    const u = getStoredUser();
    setUser(u as any);
    if (!u && typeof window !== "undefined") {
      const token = localStorage.getItem("visionid_token");
      if (!token) router.push("/login");
    }
  }, [router]);

  const logout = () => {
    clearAuth();
    router.push("/login");
  };

  return (
    <div className="min-h-screen bg-transparent text-white">
      <div className="pointer-events-none fixed inset-0 bg-grid-fine bg-[length:42px_42px] opacity-[0.04]" />
      <div className="relative flex">
        <aside className={cn("sticky top-0 hidden h-screen shrink-0 border-r border-white/10 bg-black/20 p-4 backdrop-blur-xl md:flex md:flex-col transition-all", open ? "w-72" : "w-24")}>
          <div className="mb-8 flex items-center gap-3">
            <div className="grid h-11 w-11 place-items-center rounded-2xl bg-indigo-500/20 text-indigo-300"><ScanFace className="h-5 w-5" /></div>
            {open && (
              <div>
                <div className="text-lg font-semibold">VisionID AI</div>
                <div className="text-xs text-slate-400">Face Registry & Recognition</div>
              </div>
            )}
          </div>
          <nav className="flex-1 space-y-1">
            {nav.map((item) => {
              const active = path === item.href;
              const Icon = item.icon;
              return (
                <Link key={item.href} href={item.href} className={cn("flex items-center gap-3 rounded-2xl px-3 py-3 text-sm transition", active ? "bg-white/10 text-white" : "text-slate-300 hover:bg-white/5")}>
                  <Icon className="h-4 w-4" />
                  {open && <span>{item.label}</span>}
                </Link>
              );
            })}
          </nav>
          <div className="space-y-3 pt-4">
            {open && (
              <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
                <div className="text-xs text-slate-400">Signed in as</div>
                <div className="mt-1 text-sm font-medium">{user?.full_name ?? "Guest"}</div>
                <div className="text-xs text-slate-500">{user?.role ?? "viewer"}</div>
              </div>
            )}
            <Button variant="outline" className="w-full justify-start gap-2" onClick={logout}><LogOut className="h-4 w-4" />{open && "Logout"}</Button>
          </div>
        </aside>

        <div className="flex min-h-screen flex-1 flex-col">
          <header className="sticky top-0 z-20 border-b border-white/10 bg-black/25 px-4 py-3 backdrop-blur-xl md:px-6">
            <div className="flex items-center justify-between gap-4">
              <div className="flex items-center gap-3">
                <Button variant="ghost" size="sm" className="md:hidden" onClick={() => setOpen((s) => !s)}><Menu className="h-4 w-4" /></Button>
                <Button variant="outline" size="sm" onClick={() => setOpen((s) => !s)} className="hidden md:inline-flex">
                  <Menu className="h-4 w-4" /> {open ? "Collapse" : "Expand"}
                </Button>
                <div className="text-sm text-slate-300">Premium AI face platform</div>
              </div>
              <div className="flex items-center gap-2">
                <Link href="/live"><Button variant="secondary" size="sm">Live Detection</Button></Link>
                <Link href="/registry"><Button size="sm">Add Person</Button></Link>
              </div>
            </div>
          </header>
          <main className="flex-1 p-4 md:p-6">
            <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.35 }}>
              {children}
            </motion.div>
          </main>
        </div>
      </div>
    </div>
  );
}
