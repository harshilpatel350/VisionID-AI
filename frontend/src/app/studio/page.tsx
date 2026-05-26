"use client";

import { useState, useRef } from "react";
import { AppShell } from "@/components/app-shell";
import { Card, CardContent, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { 
  ScanFace, Upload, Sparkles, Smile, Eye, AlertTriangle, Info, Trash2, ShieldAlert
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

export default function StudioPage() {
  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<any[] | null>(null);
  const [imgMeta, setImgMeta] = useState({ naturalWidth: 0, naturalHeight: 0 });
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      setFile(selectedFile);
      setPreviewUrl(URL.createObjectURL(selectedFile));
      setResults(null);
      setErrorMessage(null);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const droppedFile = e.dataTransfer.files?.[0];
    if (droppedFile && droppedFile.type.startsWith("image/")) {
      setFile(droppedFile);
      setPreviewUrl(URL.createObjectURL(droppedFile));
      setResults(null);
      setErrorMessage(null);
    }
  };

  const clearImage = () => {
    setFile(null);
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setPreviewUrl(null);
    setResults(null);
    setErrorMessage(null);
  };

  const runRecognition = async () => {
    if (!file) return;
    setLoading(true);
    setErrorMessage(null);
    const fd = new FormData();
    fd.append("image", file);
    
    try {
      const res = await api.post("/recognition/image", fd, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      // The Axios interceptor unwraps success envelope, returning the data array directly
      setResults(res.data || []);
    } catch (err: any) {
      console.error(err);
      setErrorMessage(err.response?.data?.detail || "An error occurred during recognition.");
    } finally {
      setLoading(false);
    }
  };

  const onImageLoad = (e: React.SyntheticEvent<HTMLImageElement>) => {
    const { naturalWidth, naturalHeight } = e.currentTarget;
    setImgMeta({ naturalWidth, naturalHeight });
  };

  return (
    <AppShell>
      <div className="flex flex-col mb-6">
        <h1 className="text-3xl font-bold tracking-tight text-white mb-1">Recognition Studio</h1>
        <p className="text-muted">Upload static images to run localized vector alignments, liveness tests, and demographic searches.</p>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Input & Preview Column */}
        <Card className="glass-violet border-primary/20 flex flex-col h-[600px]">
          <CardTitle className="text-white flex items-center justify-between">
            <span>Image Workbench</span>
            {previewUrl && (
              <Button variant="ghost" size="sm" onClick={clearImage} className="text-rose-400 hover:text-rose-300 hover:bg-rose-500/10">
                <Trash2 className="h-4 w-4 mr-1.5" /> Clear Image
              </Button>
            )}
          </CardTitle>
          <CardContent className="mt-4 flex-1 flex flex-col relative min-h-0">
            {!previewUrl ? (
              <div 
                onClick={() => fileInputRef.current?.click()}
                onDragOver={handleDragOver}
                onDrop={handleDrop}
                className="flex-1 border-2 border-dashed border-primary/20 hover:border-primary/40 rounded-2xl flex flex-col items-center justify-center p-6 text-center cursor-pointer transition-all duration-300 group hover:bg-primary/5"
              >
                <div className="p-4 rounded-full bg-primary/10 text-accent group-hover:scale-110 transition-transform duration-300 shadow-glow-violet/10 mb-4">
                  <Upload className="h-8 w-8" />
                </div>
                <h3 className="text-base font-semibold text-white mb-1">Upload Face Image</h3>
                <p className="text-xs text-muted max-w-xs">Drag and drop your image here, or click to browse files from your computer</p>
                <input 
                  type="file" 
                  ref={fileInputRef} 
                  onChange={handleFileChange} 
                  accept="image/*" 
                  className="hidden" 
                />
              </div>
            ) : (
              <div className="flex-1 flex flex-col justify-between min-h-0">
                <div className="relative flex-1 bg-black/40 rounded-2xl overflow-hidden border border-primary/10 flex items-center justify-center p-2 min-h-0">
                  <div className="relative max-h-full max-w-full">
                    <img 
                      src={previewUrl} 
                      alt="Preview" 
                      onLoad={onImageLoad}
                      className="max-h-[380px] max-w-full rounded-lg object-contain" 
                    />
                    
                    {/* Bounding box overlays */}
                    {results && results.map((match, idx) => {
                      if (!match.bbox || !imgMeta.naturalWidth) return null;
                      const { x1, y1, x2, y2 } = match.bbox;
                      const left = (x1 / imgMeta.naturalWidth) * 100;
                      const top = (y1 / imgMeta.naturalHeight) * 100;
                      const width = ((x2 - x1) / imgMeta.naturalWidth) * 100;
                      const height = ((y2 - y1) / imgMeta.naturalHeight) * 100;

                      return (
                        <motion.div
                          key={idx}
                          initial={{ opacity: 0, scale: 0.8 }}
                          animate={{ opacity: 1, scale: 1 }}
                          className="absolute border-2 border-primary rounded shadow-glow-violet bg-primary/5"
                          style={{
                            left: `${left}%`,
                            top: `${top}%`,
                            width: `${width}%`,
                            height: `${height}%`,
                          }}
                        >
                          <div className="absolute -top-6 left-0 bg-primary/90 text-[10px] font-bold text-white px-2 py-0.5 rounded whitespace-nowrap backdrop-blur border border-primary/20 shadow-md">
                            {match.full_name} ({(match.confidence * 100).toFixed(0)}%)
                          </div>
                        </motion.div>
                      );
                    })}
                  </div>
                </div>

                <div className="pt-4 flex gap-3">
                  <Button 
                    onClick={runRecognition} 
                    disabled={loading} 
                    className="flex-1 bg-primary hover:bg-primary/90 text-white shadow-glow-violet h-11"
                  >
                    {loading ? (
                      <span className="flex items-center gap-2">
                        <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                        Running Analysis...
                      </span>
                    ) : (
                      <span className="flex items-center gap-2">
                        <Sparkles className="h-4 w-4 text-accent" />
                        Run AI Recognition
                      </span>
                    )}
                  </Button>
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Results Analysis Column */}
        <Card className="glass-violet border-primary/20 flex flex-col h-[600px]">
          <CardTitle className="text-white">Analysis Results</CardTitle>
          <CardContent className="mt-4 flex-1 overflow-y-auto pr-1 space-y-4 min-h-0">
            <AnimatePresence mode="wait">
              {loading ? (
                <motion.div 
                  initial={{ opacity: 0 }} 
                  animate={{ opacity: 1 }} 
                  exit={{ opacity: 0 }}
                  className="h-full flex flex-col items-center justify-center text-center p-6"
                >
                  <div className="relative w-16 h-16 mb-4">
                    <div className="absolute inset-0 rounded-full border-4 border-primary/20" />
                    <div className="absolute inset-0 rounded-full border-4 border-primary border-t-transparent animate-spin" />
                  </div>
                  <h3 className="text-base font-semibold text-white mb-1">Analyzing Embeddings</h3>
                  <p className="text-xs text-muted max-w-xs">Comparing localized face encodings against registered vector indices...</p>
                </motion.div>
              ) : errorMessage ? (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="p-4 rounded-xl border border-rose-500/20 bg-rose-500/10 text-rose-300 text-sm flex gap-3"
                >
                  <AlertTriangle className="h-5 w-5 shrink-0" />
                  <div>
                    <div className="font-semibold">Analysis Failed</div>
                    <div className="text-xs mt-1 text-rose-300/80">{errorMessage}</div>
                  </div>
                </motion.div>
              ) : results === null ? (
                <motion.div 
                  initial={{ opacity: 0 }} 
                  animate={{ opacity: 1 }}
                  className="h-full flex flex-col items-center justify-center text-center p-6 border border-dashed border-primary/10 rounded-2xl"
                >
                  <ScanFace className="h-10 w-10 text-primary mb-3 animate-pulse" />
                  <h3 className="text-sm font-semibold text-white mb-1">Awaiting Data</h3>
                  <p className="text-xs text-muted max-w-xs">Upload an image file and press 'Run AI Recognition' to extract intelligence details.</p>
                </motion.div>
              ) : results.length === 0 ? (
                <motion.div 
                  initial={{ opacity: 0 }} 
                  animate={{ opacity: 1 }}
                  className="h-full flex flex-col items-center justify-center text-center p-6 border border-dashed border-rose-500/25 rounded-2xl bg-rose-500/5"
                >
                  <ShieldAlert className="h-10 w-10 text-rose-300 mb-3" />
                  <h3 className="text-sm font-semibold text-white mb-1">No Faces Detected</h3>
                  <p className="text-xs text-muted max-w-xs">Our vision system could not locate any clear human faces in this photo. Try using a brighter, higher-resolution capture.</p>
                </motion.div>
              ) : (
                <motion.div 
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="space-y-4"
                >
                  <div className="text-xs text-accent uppercase font-bold tracking-widest mb-1 flex items-center gap-2">
                    <Info className="h-3.5 w-3.5" /> Found {results.length} Face{results.length > 1 ? "s" : ""}
                  </div>
                  {results.map((match, idx) => (
                    <Card key={idx} className="bg-black/35 border-primary/10 p-4 rounded-xl hover:border-primary/20 transition-all duration-300">
                      <div className="flex justify-between items-start mb-3">
                        <div>
                          <h4 className="text-base font-bold text-white flex items-center gap-2">
                            {match.full_name}
                            {match.is_unknown ? (
                              <Badge className="bg-orange-500/10 text-orange-300 border-none text-[10px]">Unknown</Badge>
                            ) : (
                              <Badge className="bg-emerald-500/10 text-emerald-300 border-none text-[10px]">Verified Match</Badge>
                            )}
                          </h4>
                          {!match.is_unknown && (
                            <p className="text-xs text-muted mt-0.5">
                              {match.department && <span>Dept: {match.department}</span>}
                              {match.title && <span> • {match.title}</span>}
                            </p>
                          )}
                        </div>
                        <div className="text-right">
                          <span className="text-xs text-muted block">Confidence</span>
                          <span className="text-lg font-extrabold text-accent">{(match.confidence * 100).toFixed(0)}%</span>
                        </div>
                      </div>

                      <div className="grid grid-cols-2 gap-3 mt-3 pt-3 border-t border-white/5 text-xs text-muted">
                        <div className="flex items-center gap-2">
                          <Smile className="h-3.5 w-3.5 text-accent" />
                          <span>Mood: <strong className="text-white capitalize">{match.mood || "N/A"}</strong></span>
                        </div>
                        <div className="flex items-center gap-2">
                          <Eye className="h-3.5 w-3.5 text-accent" />
                          <span>Liveness: <strong className={match.liveness_suspicious ? "text-rose-300" : "text-white"}>{match.liveness_score !== null ? `${(match.liveness_score * 100).toFixed(0)}%` : "N/A"}</strong></span>
                        </div>
                        <div className="flex items-center gap-2">
                          <ScanFace className="h-3.5 w-3.5 text-accent" />
                          <span>Quality: <strong className="text-white">{(match.quality_score * 100).toFixed(0)}%</strong></span>
                        </div>
                        <div className="flex items-center gap-2">
                          <Sparkles className="h-3.5 w-3.5 text-accent" />
                          <span>Enhanced: <strong className="text-white">{match.is_enhanced ? "Yes" : "No"}</strong></span>
                        </div>
                      </div>

                      {match.liveness_suspicious && (
                        <div className="mt-3 p-2 rounded-lg bg-rose-500/10 border border-rose-500/20 text-[10px] text-rose-300 flex items-center gap-2">
                          <AlertTriangle className="h-3.5 w-3.5 shrink-0" />
                          <span>Warning: Liveness analysis returned suspicious results (possible photo replay attack).</span>
                        </div>
                      )}
                    </Card>
                  ))}
                </motion.div>
              )}
            </AnimatePresence>
          </CardContent>
        </Card>
      </div>
    </AppShell>
  );
}
