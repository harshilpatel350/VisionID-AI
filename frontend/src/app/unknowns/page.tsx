"use client";

import { useEffect, useState } from "react";
import { AppShell } from "@/components/app-shell";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Dialog, DialogContent, DialogTitle } from "@/components/ui/dialog";
import { api, API_BASE } from "@/lib/api";
import { CheckCircle2, UserPlus } from "lucide-react";
import { MoodChip } from "@/components/ui/mood-chip";

function formatDistanceToNow(dateInput: Date, _options?: { addSuffix?: boolean }) {
  const now = new Date();
  const diffInMs = now.getTime() - dateInput.getTime();
  const diffInSecs = Math.floor(diffInMs / 1000);
  const diffInMins = Math.floor(diffInSecs / 60);
  const diffInHours = Math.floor(diffInMins / 60);
  const diffInDays = Math.floor(diffInHours / 24);

  if (diffInSecs < 60) return "just now";
  if (diffInMins < 60) return `${diffInMins}m ago`;
  if (diffInHours < 24) return `${diffInHours}h ago`;
  if (diffInDays === 1) return "yesterday";
  return `${diffInDays}d ago`;
}

interface UnknownFace {
  id: number;
  timestamp: string;
  source_type: string;
  source_ref: string | null;
  snapshot_path: string;
  confidence: number;
  mood: string | null;
  liveness_score: number | null;
  is_reviewed: boolean;
  registered_as_person_id: number | null;
}

export default function UnknownsPage() {
  const [faces, setFaces] = useState<UnknownFace[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<"all" | "pending" | "reviewed">("pending");
  const [exportFilters, setExportFilters] = useState({ start: "", end: "", mood: "" });
  const [registerOpen, setRegisterOpen] = useState(false);
  const [selectedFace, setSelectedFace] = useState<UnknownFace | null>(null);
  const [registering, setRegistering] = useState(false);
  const [registerForm, setRegisterForm] = useState({
    full_name: "",
    department: "",
    title: "",
    age: "",
    gender: "",
    tags: "",
    notes: "",
  });
  const [similarMap, setSimilarMap] = useState<Record<number, any[]>>({});

  const loadFaces = async () => {
    setLoading(true);
    try {
      let url = "/unknowns?size=50";
      if (filter === "pending") url += "&is_reviewed=false";
      if (filter === "reviewed") url += "&is_reviewed=true";
      const res = await api.get(url);
      setFaces(res.data.items || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadFaces();
  }, [filter]);

  const handleMarkReviewed = async (id: number) => {
    try {
      await api.put(`/unknowns/${id}/review`);
      loadFaces();
    } catch (err) {
      console.error("Failed to mark reviewed", err);
    }
  };

  const exportUnknowns = async (format: "csv" | "xlsx") => {
    const params: any = {};
    if (filter === "pending") params.is_reviewed = false;
    if (filter === "reviewed") params.is_reviewed = true;
    if (exportFilters.start) params.start = exportFilters.start;
    if (exportFilters.end) params.end = exportFilters.end;
    if (exportFilters.mood) params.mood = exportFilters.mood;
    const mime = format === "csv" ? "text/csv" : "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet";
    const res = await api.get(`/exports/unknowns.${format}`, { params, responseType: "blob" });
    const blob = new Blob([res.data], { type: mime });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement("a");
    const stamp = new Date().toISOString().slice(0, 10);
    link.href = url;
    link.download = `unknowns_${stamp}.${format}`;
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  };

  const openRegister = (face: UnknownFace) => {
    setSelectedFace(face);
    setRegisterForm({
      full_name: "",
      department: "",
      title: "",
      age: "",
      gender: "",
      tags: "",
      notes: "",
    });
    setRegisterOpen(true);
  };

  const submitRegister = async () => {
    if (!selectedFace || !registerForm.full_name.trim()) return;
    setRegistering(true);
    try {
      await api.post(`/unknowns/${selectedFace.id}/register`, {
        ...registerForm,
        age: registerForm.age ? Number(registerForm.age) : null,
      });
      setRegisterOpen(false);
      loadFaces();
    } catch (err) {
      console.error("Failed to register face", err);
    } finally {
      setRegistering(false);
    }
  };

  const loadSimilar = async (id: number) => {
    try {
      const res = await api.get(`/unknowns/${id}/similar`);
      const items = res.data?.items ?? res.data?.data?.items ?? [];
      setSimilarMap((prev) => ({ ...prev, [id]: items }));
    } catch (err) {
      console.error("Failed to fetch similar faces", err);
    }
  };

  return (
    <AppShell>
      <div className="flex flex-col mb-6">
        <h1 className="text-3xl font-bold tracking-tight text-white mb-1 flex items-center gap-2">
          Unknown Faces <Badge className="rounded-full bg-rose-500/20 text-rose-300 border border-rose-500/40">{faces.length > 0 && filter === 'pending' ? faces.length : ''}</Badge>
        </h1>
        <p className="text-muted">Review unidentified individuals captured by the live webcam or group photos.</p>
      </div>

      <div className="flex flex-wrap items-center justify-between gap-3 mb-6">
        <div className="flex items-center gap-2">
          <Button 
            variant={filter === "pending" ? "default" : "secondary"} 
            onClick={() => setFilter("pending")}
            className={filter === "pending" ? "bg-primary hover:bg-primary/90 text-white shadow-glow-violet" : "bg-primary/20 text-accent hover:bg-primary/30 border border-primary/30"}
          >
            Pending Review
          </Button>
          <Button 
            variant={filter === "reviewed" ? "default" : "secondary"} 
            onClick={() => setFilter("reviewed")}
            className={filter === "reviewed" ? "bg-primary hover:bg-primary/90 text-white shadow-glow-violet" : "bg-primary/20 text-accent hover:bg-primary/30 border border-primary/30"}
          >
            Reviewed
          </Button>
          <Button 
            variant={filter === "all" ? "default" : "secondary"} 
            onClick={() => setFilter("all")}
            className={filter === "all" ? "bg-primary hover:bg-primary/90 text-white shadow-glow-violet" : "bg-primary/20 text-accent hover:bg-primary/30 border border-primary/30"}
          >
            All
          </Button>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" className="border-primary/20 text-accent" onClick={() => exportUnknowns("csv")}>Export CSV</Button>
          <Button variant="outline" className="border-primary/20 text-accent" onClick={() => exportUnknowns("xlsx")}>Export XLSX</Button>
        </div>
      </div>
      <div className="grid gap-3 md:grid-cols-[1fr_1fr_1fr_auto] mb-6">
        <Input
          type="datetime-local"
          value={exportFilters.start}
          onChange={(e) => setExportFilters({ ...exportFilters, start: e.target.value })}
          className="bg-black/20 border-white/10"
        />
        <Input
          type="datetime-local"
          value={exportFilters.end}
          onChange={(e) => setExportFilters({ ...exportFilters, end: e.target.value })}
          className="bg-black/20 border-white/10"
        />
        <Input
          placeholder="Mood filter"
          value={exportFilters.mood}
          onChange={(e) => setExportFilters({ ...exportFilters, mood: e.target.value })}
          className="bg-black/20 border-white/10"
        />
        <Button variant="secondary" className="bg-primary/20 text-accent border border-primary/30" onClick={() => exportUnknowns("csv")}>Export with Filters</Button>
      </div>

      {loading ? (
        <div className="flex justify-center p-12">
          <div className="w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin"></div>
        </div>
      ) : faces.length === 0 ? (
        <Card className="flex flex-col items-center justify-center p-12 text-center glass-violet border-dashed border-primary/20">
          <div className="w-16 h-16 bg-emerald-500/10 text-emerald-400 rounded-full flex items-center justify-center mb-4">
            <CheckCircle2 size={32} />
          </div>
          <h3 className="text-lg font-medium text-white mb-1">All clear!</h3>
          <p className="text-muted">No unknown faces found for the selected filter.</p>
        </Card>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {faces.map((face) => (
            <Card key={face.id} className="overflow-hidden glass-violet border-primary/20 flex flex-col transition-all hover:shadow-glow-violet">
              <div className="relative aspect-square bg-black overflow-hidden group">
                <img 
                  src={`${API_BASE}/${face.snapshot_path}`} 
                  alt="Unknown Face" 
                  className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent"></div>
                <div className="absolute bottom-3 left-3 right-3 flex justify-between items-end">
                  <div className="text-xs text-white/80 flex flex-col">
                    <span className="font-semibold text-white">{formatDistanceToNow(new Date(face.timestamp), { addSuffix: true })}</span>
                    <span className="capitalize">{face.source_type}</span>
                  </div>
                  {face.mood && <MoodChip mood={face.mood} className="shadow-lg backdrop-blur-md" />}
                </div>
                {!face.is_reviewed && (
                  <div className="absolute top-3 right-3">
                    <span className="flex h-3 w-3 relative">
                      <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
                      <span className="relative inline-flex rounded-full h-3 w-3 bg-red-500"></span>
                    </span>
                  </div>
                )}
              </div>
              
              <div className="p-4 flex-1 flex flex-col">
                <div className="flex flex-wrap gap-2 mb-4">
                  {face.liveness_score !== null && (
                    <Badge className={face.liveness_score > 0.5 ? "text-green-400 border-green-500/30 bg-green-500/5" : "text-red-400 border-red-500/30 bg-red-500/5"}>
                      Liveness: {(face.liveness_score * 100).toFixed(0)}%
                    </Badge>
                  )}
                  {face.confidence && (
                    <Badge className="text-blue-300 border-blue-500/30 bg-blue-500/5">
                      Conf: {(face.confidence * 100).toFixed(0)}%
                    </Badge>
                  )}
                </div>
                
                <div className="mt-auto pt-4 border-t border-white/5 flex gap-2">
                  {!face.is_reviewed ? (
                    <>
                      <Button 
                        variant="secondary" 
                        size="sm" 
                        className="flex-1"
                        onClick={() => handleMarkReviewed(face.id)}
                      >
                        Dismiss
                      </Button>
                      <Button 
                        variant="default" 
                        size="sm" 
                        className="flex-1 gap-1"
                        onClick={() => openRegister(face)}
                      >
                        <UserPlus size={14} /> Register
                      </Button>
                    </>
                  ) : (
                    <div className="w-full text-center text-xs text-muted flex items-center justify-center gap-1 py-1.5">
                      <CheckCircle2 size={14} className="text-green-500" /> Reviewed
                      {face.registered_as_person_id && ` · Registered`}
                    </div>
                  )}
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  className="mt-2 text-xs text-muted hover:text-white"
                  onClick={() => loadSimilar(face.id)}
                >
                  Find Similar
                </Button>
                {similarMap[face.id]?.length ? (
                  <div className="mt-3 grid grid-cols-3 gap-2">
                    {similarMap[face.id].map((hit: any) => (
                      <div key={hit.id} className="rounded-lg overflow-hidden border border-primary/20 bg-black/30">
                        <img src={`${API_BASE}/${hit.snapshot_path}`} alt="Similar" className="h-16 w-full object-cover" />
                        <div className="px-2 py-1 text-[10px] text-muted">{(hit.similarity * 100).toFixed(1)}%</div>
                      </div>
                    ))}
                  </div>
                ) : null}
              </div>
            </Card>
          ))}
        </div>
      )}
      <Dialog open={registerOpen} onOpenChange={setRegisterOpen}>
        <DialogContent className="max-w-lg bg-[rgb(var(--panel))]/90 border-primary/20 text-white">
          <DialogTitle className="text-lg font-semibold">Register Unknown Face</DialogTitle>
          <div className="grid gap-3 mt-4">
            <Input placeholder="Full name *" value={registerForm.full_name} onChange={(e) => setRegisterForm({ ...registerForm, full_name: e.target.value })} className="bg-black/20 border-white/10" />
            <div className="grid grid-cols-2 gap-2">
              <Input placeholder="Department" value={registerForm.department} onChange={(e) => setRegisterForm({ ...registerForm, department: e.target.value })} className="bg-black/20 border-white/10" />
              <Input placeholder="Title" value={registerForm.title} onChange={(e) => setRegisterForm({ ...registerForm, title: e.target.value })} className="bg-black/20 border-white/10" />
            </div>
            <div className="grid grid-cols-3 gap-2">
              <Input placeholder="Age" type="number" value={registerForm.age} onChange={(e) => setRegisterForm({ ...registerForm, age: e.target.value })} className="bg-black/20 border-white/10" />
              <Input placeholder="Gender" value={registerForm.gender} onChange={(e) => setRegisterForm({ ...registerForm, gender: e.target.value })} className="bg-black/20 border-white/10" />
              <Input placeholder="Tags" value={registerForm.tags} onChange={(e) => setRegisterForm({ ...registerForm, tags: e.target.value })} className="bg-black/20 border-white/10" />
            </div>
            <Input placeholder="Notes" value={registerForm.notes} onChange={(e) => setRegisterForm({ ...registerForm, notes: e.target.value })} className="bg-black/20 border-white/10" />
            <div className="flex gap-2 pt-2">
              <Button variant="secondary" className="flex-1" onClick={() => setRegisterOpen(false)}>Cancel</Button>
              <Button className="flex-1 bg-primary text-white" onClick={submitRegister} disabled={registering || !registerForm.full_name.trim()}>
                {registering ? "Registering..." : "Register"}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </AppShell>
  );
}
