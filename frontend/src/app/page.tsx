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
    <main className="min-h-screen relative overflow-hidden bg-transparent">
      {/* Decorative radial glows */}
      <div className="absolute top-[-10%] left-[-10%] w-[50%] h-[50%] rounded-full bg-primary/20 blur-[120px] pointer-events-none" />
      <div className="absolute bottom-[-10%] right-[-10%] w-[50%] h-[50%] rounded-full bg-accent/15 blur-[120px] pointer-events-none" />

      <section className="relative mx-auto max-w-7xl px-6 py-10 z-10">
        <div className="flex items-center justify-between">
          <div className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
            <div className="h-8 w-8 grid place-items-center rounded-xl bg-primary/20 text-accent shadow-glow-violet"><ScanFace className="h-4 w-4" /></div>
            <span>VisionID <span className="text-accent">AI</span></span>
          </div>
          <div className="flex gap-3">
            <Link href="/login"><Button variant="outline" className="border-primary/20 text-accent hover:bg-primary/20">Login</Button></Link>
            <Link href="/register"><Button className="bg-primary hover:bg-primary/90 text-white shadow-glow-violet">Get Started</Button></Link>
          </div>
        </div>

        <div className="mt-20 grid gap-12 lg:grid-cols-[1.2fr_.8fr] lg:items-center">
          <div>
            <div className="inline-flex items-center gap-2 rounded-full border border-primary/30 bg-primary/10 px-4 py-2 text-xs text-accent shadow-glow-violet/10">
              <Sparkles className="h-4 w-4 text-accent animate-pulse" /> Production-grade face intelligence platform
            </div>
            <h1 className="mt-6 max-w-3xl text-5xl font-extrabold tracking-tight md:text-7xl bg-gradient-to-r from-white via-accent to-primary bg-clip-text text-transparent leading-[1.15]">
              Face Registry and Recognition with real-time AI.
            </h1>
            <p className="mt-6 max-w-2xl text-lg text-muted">
              VisionID AI combines face registry, vector search, webcam recognition, analytics, and audit history in one premium SaaS-style platform.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <Link href="/dashboard"><Button size="lg" className="bg-primary hover:bg-primary/90 text-white shadow-glow-violet">Open Dashboard <ArrowRight className="ml-2 h-4 w-4" /></Button></Link>
              <Link href="/live"><Button size="lg" variant="secondary" className="bg-primary/20 text-accent hover:bg-primary/30 border border-primary/30">Try Live Webcam</Button></Link>
            </div>
          </div>

          <Card className="relative overflow-hidden glass-violet border-primary/20">
            <CardContent className="p-0">
              <div className="grid gap-4 p-6">
                <div className="rounded-3xl border border-primary/25 bg-gradient-to-br from-primary/30 via-accent/10 to-transparent p-6 shadow-glow-violet/5">
                  <div className="text-xs font-semibold text-accent uppercase tracking-wider">Recognition pipeline</div>
                  <div className="mt-2 text-2xl font-bold text-white tracking-tight">Detection → Alignment → Embedding → Match</div>
                  <div className="mt-3 text-sm text-muted">FAISS vector similarity, unknown face handling, and confidence thresholds.</div>
                </div>
                <div className="grid gap-3 md:grid-cols-2">
                  {features.map((f) => {
                    const Icon = f.icon;
                    return (
                      <div key={f.title} className="rounded-2xl border border-primary/10 bg-primary/5 p-4 hover:border-primary/35 hover:shadow-glow-violet transition-all duration-300">
                        <Icon className="h-5 w-5 text-accent" />
                        <div className="mt-3 font-semibold text-white">{f.title}</div>
                        <div className="mt-1 text-xs text-muted">{f.text}</div>
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
