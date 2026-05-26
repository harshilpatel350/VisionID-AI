"use client";

import { AppShell } from "@/components/app-shell";
import { WebcamModal } from "@/components/webcam-modal";
import { Card, CardContent, CardTitle } from "@/components/ui/card";

export default function LivePage() {
  return (
    <AppShell>
      <div className="flex flex-col h-[calc(100vh-6rem)]">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-3xl font-bold tracking-tight text-white mb-1">Live Intelligence</h1>
            <p className="text-muted">Real-time facial recognition with mood analysis and liveness detection.</p>
          </div>
          <WebcamModal />
        </div>
        
        <div className="flex-1 rounded-3xl bg-black/40 border border-primary/20 overflow-hidden flex flex-col items-center justify-center relative shadow-glow-violet">
          <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,rgba(138,99,242,0.06),transparent)] pointer-events-none"></div>
          <div className="text-center p-8 max-w-md z-10">
            <div className="w-20 h-20 bg-primary/15 text-accent rounded-full flex items-center justify-center mx-auto mb-6 ring-1 ring-primary/30 shadow-glow-violet">
              <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14.5 4h-5L7 7H4a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2h-3l-2.5-3z"/><circle cx="12" cy="13" r="3"/></svg>
            </div>
            <h2 className="text-xl font-semibold text-white mb-3">Live Streaming Standby</h2>
            <p className="text-muted text-sm mb-6 leading-relaxed">
              Open the Webcam Studio to begin processing real-time video frames. The system will detect faces, track identities across frames, and analyze emotion and liveness.
            </p>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
