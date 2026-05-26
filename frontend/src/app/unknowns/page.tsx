"use client";

import { useEffect, useState } from "react";
import { AppShell } from "@/components/app-shell";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { api, API_BASE } from "@/lib/api";
import { CheckCircle2, UserPlus, AlertTriangle } from "lucide-react";
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

  return (
    <AppShell>
      <div className="flex flex-col mb-6">
        <h1 className="text-3xl font-bold tracking-tight text-white mb-1 flex items-center gap-2">
          Unknown Faces <Badge className="rounded-full bg-rose-500/20 text-rose-300 border border-rose-500/40">{faces.length > 0 && filter === 'pending' ? faces.length : ''}</Badge>
        </h1>
        <p className="text-muted">Review unidentified individuals captured by the live webcam or group photos.</p>
      </div>

      <div className="flex items-center gap-2 mb-6">
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
                        // In a full implementation, this would open a dialog to register the person
                        onClick={() => alert("Registration modal would open here in full version")}
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
              </div>
            </Card>
          ))}
        </div>
      )}
    </AppShell>
  );
}
