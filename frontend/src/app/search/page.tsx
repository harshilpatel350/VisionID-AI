"use client";

import { useState } from "react";
import { AppShell } from "@/components/app-shell";
import { Card, CardContent, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";

export default function SearchPage() {
  const [file, setFile] = useState<File | null>(null);
  const [result, setResult] = useState<any>(null);

  const submit = async () => {
    if (!file) return;
    const fd = new FormData();
    fd.append("image", file);
    const { data } = await api.post("/faces/search", fd, { headers: { "Content-Type": "multipart/form-data" } });
    setResult(data);
  };

  return (
    <AppShell>
      <Card className="glass-violet border-primary/20">
        <CardTitle className="text-white">Search Console</CardTitle>
        <CardContent className="mt-4 space-y-4">
          <Input type="file" accept="image/*" onChange={(e) => setFile(e.target.files?.[0] ?? null)} className="bg-black/20 border-white/10 focus-visible:ring-primary" />
          <Button onClick={submit} className="bg-primary hover:bg-primary/90 text-white shadow-glow-violet">Search identity</Button>
          <pre className="overflow-auto rounded-2xl border border-primary/20 bg-black/30 p-4 text-xs text-slate-200">{JSON.stringify(result, null, 2)}</pre>
        </CardContent>
      </Card>
    </AppShell>
  );
}
