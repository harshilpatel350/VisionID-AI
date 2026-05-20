"use client";

import { AppShell } from "@/components/app-shell";
import { WebcamModal } from "@/components/webcam-modal";
import { Card, CardContent, CardTitle } from "@/components/ui/card";

export default function LivePage() {
  return (
    <AppShell>
      <Card>
        <CardTitle>Live Webcam Detection</CardTitle>
        <CardContent className="mt-4">
          <WebcamModal />
          <p className="mt-4 text-sm text-slate-400">Webcam frames are streamed through WebSockets and processed locally.</p>
        </CardContent>
      </Card>
    </AppShell>
  );
}
