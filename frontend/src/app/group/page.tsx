"use client";

import { useState } from "react";
import { AppShell } from "@/components/app-shell";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { api, API_BASE } from "@/lib/api";
import { UploadCloud, Users, Smile, UserX } from "lucide-react";
import { FaceTrackerCard, TrackerMatch } from "@/components/ui/face-tracker-card";

export default function GroupPage() {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const selected = e.target.files[0];
      setFile(selected);
      setPreview(URL.createObjectURL(selected));
      setResult(null);
      setError(null);
    }
  };

  const handleAnalyze = async () => {
    if (!file) return;
    setLoading(true);
    setError(null);
    
    const fd = new FormData();
    fd.append("file", file);
    
    try {
      const res = await api.post("/group/analyze", fd);
      setResult(res.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to analyze image");
    } finally {
      setLoading(false);
    }
  };

  return (
    <AppShell>
      <div className="flex flex-col mb-6">
        <h1 className="text-3xl font-bold tracking-tight text-white mb-1">Group Photo Analysis</h1>
        <p className="text-muted">Upload a photo of a group or crowd to detect all faces, identify known people, and analyze moods.</p>
      </div>

      <div className="grid md:grid-cols-[1fr_350px] gap-6">
        <div className="space-y-6">
          <Card className="p-6 glass-violet border-primary/20">
            {!preview ? (
              <div className="border-2 border-dashed border-primary/20 rounded-xl p-12 text-center hover:bg-primary/5 transition-colors cursor-pointer relative">
                <Input 
                  type="file" 
                  accept="image/*" 
                  className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                  onChange={handleFileChange}
                />
                <UploadCloud className="w-12 h-12 mx-auto mb-4 text-muted" />
                <h3 className="text-lg font-medium text-white mb-1">Upload Group Photo</h3>
                <p className="text-sm text-muted">JPEG, PNG up to 10MB</p>
              </div>
            ) : (
              <div className="space-y-4">
                <div className="relative rounded-xl overflow-hidden bg-black aspect-video flex items-center justify-center">
                  <img 
                    src={result?.annotated_image_url ? `${API_BASE}/${result.annotated_image_url}` : preview} 
                    alt="Preview" 
                    className="max-w-full max-h-[60vh] object-contain"
                  />
                  {loading && (
                    <div className="absolute inset-0 bg-black/60 flex flex-col items-center justify-center backdrop-blur-sm">
                      <div className="w-10 h-10 border-4 border-primary border-t-transparent rounded-full animate-spin mb-4" />
                      <p className="font-medium text-white">Analyzing Crowd...</p>
                    </div>
                  )}
                </div>
                <div className="flex gap-3">
                  <Button 
                    className="flex-1 bg-primary hover:bg-primary/90 text-white shadow-glow-violet" 
                    size="lg" 
                    onClick={handleAnalyze} 
                    disabled={loading || !!result}
                  >
                    Analyze Image
                  </Button>
                  <Button 
                    variant="outline" 
                    size="lg"
                    className="border-primary/20 text-accent hover:bg-primary/10" 
                    onClick={() => {
                      setFile(null);
                      setPreview(null);
                      setResult(null);
                    }}
                  >
                    Reset
                  </Button>
                </div>
                {error && <p className="text-red-400 text-sm p-3 bg-red-400/10 rounded-lg">{error}</p>}
              </div>
            )}
          </Card>
        </div>

        <div>
          {result ? (
            <div className="space-y-6">
              <Card className="p-5 glass-violet border-primary/20">
                <h3 className="text-sm font-semibold uppercase tracking-wider text-muted mb-4">Summary</h3>
                <div className="grid grid-cols-2 gap-3">
                  <div className="bg-primary/10 p-3 rounded-lg border border-primary/20 flex flex-col">
                    <span className="text-3xl font-bold text-primary">{result.summary.total_faces}</span>
                    <span className="text-xs text-primary/80 font-medium uppercase mt-1 flex items-center gap-1">
                      <Users size={12} /> Total Faces
                    </span>
                  </div>
                  <div className="bg-orange-500/10 p-3 rounded-lg border border-orange-500/20 flex flex-col">
                    <span className="text-3xl font-bold text-orange-500">{result.summary.unknown_faces}</span>
                    <span className="text-xs text-orange-500/80 font-medium uppercase mt-1 flex items-center gap-1">
                      <UserX size={12} /> Unknowns
                    </span>
                  </div>
                </div>
                
                {Object.keys(result.summary.mood_distribution || {}).length > 0 && (
                  <div className="mt-4 pt-4 border-t border-primary/20">
                    <h4 className="text-xs font-semibold text-muted mb-2 flex items-center gap-1">
                      <Smile size={12} /> Mood Distribution
                    </h4>
                    <div className="flex flex-wrap gap-2">
                      {Object.entries(result.summary.mood_distribution).map(([mood, count]) => (
                        <div key={mood} className="px-2 py-1 bg-primary/10 rounded-md text-xs flex items-center gap-1.5 border border-primary/20">
                          <span className="capitalize text-white font-medium">{mood}</span>
                          <span className="text-muted">{count as number}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </Card>

              <div className="space-y-3">
                <h3 className="text-sm font-semibold uppercase tracking-wider text-muted mb-2 flex items-center justify-between">
                  <span>Detected Faces</span>
                  <span className="bg-primary/20 text-accent px-2 py-0.5 rounded-full text-xs">{result.faces.length}</span>
                </h3>
                <div className="space-y-3 max-h-[600px] overflow-y-auto pr-1 pb-4">
                  {result.faces.map((face: any, i: number) => (
                    <FaceTrackerCard key={i} match={face as TrackerMatch} />
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <Card className="h-full min-h-[400px] flex flex-col items-center justify-center p-6 text-center text-muted border-dashed glass-violet border-primary/20">
              <Users className="w-12 h-12 mb-4 opacity-50" />
              <h3 className="font-medium text-white mb-1">Waiting for Analysis</h3>
              <p className="text-sm">Upload a photo and click analyze to see results here.</p>
            </Card>
          )}
        </div>
      </div>
    </AppShell>
  );
}
