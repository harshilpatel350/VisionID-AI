import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { ScanFace, Shield, Sparkles, Activity, Globe2, ArrowRight } from "lucide-react";

const features = [
  { icon: ScanFace, title: "Face Registry", text: "Register identities, samples, and embeddings with duplicate prevention." },
  { icon: Shield, title: "Secure Access", text: "JWT login, role-based permissions, audit trails, and admin controls." },
  { icon: Activity, title: "Realtime Analytics", text: "Recognition logs, confidence trends, and live monitoring panels." },
  { icon: Globe2, title: "Modern SaaS UI", text: "Glassmorphism layout, animated motion, and responsive experience." },
];

export default function LandingPage() {
  return (
    <main className="min-h-screen">
      <section className="mx-auto max-w-7xl px-6 py-10">
        <div className="flex items-center justify-between">
          <div className="text-xl font-semibold">VisionID AI</div>
          <div className="flex gap-3">
            <Link href="/login"><Button variant="outline">Login</Button></Link>
            <Link href="/register"><Button>Get Started</Button></Link>
          </div>
        </div>

        <div className="mt-20 grid gap-12 lg:grid-cols-[1.2fr_.8fr] lg:items-center">
          <div>
            <div className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-4 py-2 text-xs text-slate-300">
              <Sparkles className="h-4 w-4 text-indigo-300" /> Production-grade face intelligence platform
            </div>
            <h1 className="mt-6 max-w-3xl text-5xl font-semibold tracking-tight md:text-7xl">
              Face Registry and Recognition with real-time AI operations.
            </h1>
            <p className="mt-6 max-w-2xl text-lg text-slate-300">
              VisionID AI combines face registry, vector search, webcam recognition, analytics, and audit history in one premium SaaS-style platform.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <Link href="/dashboard"><Button size="lg">Open Dashboard <ArrowRight className="ml-2 h-4 w-4" /></Button></Link>
              <Link href="/live"><Button size="lg" variant="secondary">Try Live Webcam</Button></Link>
            </div>
          </div>

          <Card className="relative overflow-hidden">
            <CardContent className="p-0">
              <div className="grid gap-4 p-6">
                <div className="rounded-3xl border border-white/10 bg-gradient-to-br from-indigo-500/20 to-fuchsia-500/10 p-6">
                  <div className="text-sm text-slate-300">Recognition pipeline</div>
                  <div className="mt-2 text-3xl font-semibold">Detection → Alignment → Embedding → Match</div>
                  <div className="mt-3 text-sm text-slate-300">FAISS vector similarity, unknown face handling, and confidence thresholds.</div>
                </div>
                <div className="grid gap-3 md:grid-cols-2">
                  {features.map((f) => {
                    const Icon = f.icon;
                    return (
                      <div key={f.title} className="rounded-2xl border border-white/10 bg-white/5 p-4">
                        <Icon className="h-5 w-5 text-indigo-300" />
                        <div className="mt-3 font-medium">{f.title}</div>
                        <div className="mt-1 text-sm text-slate-400">{f.text}</div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </section>
    </main>
  );
}
