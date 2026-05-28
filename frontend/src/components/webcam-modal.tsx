"use client";

import { useEffect, useRef, useState } from "react";
import { Dialog, DialogContent, DialogTrigger, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { API_BASE, api } from "@/lib/api";

type RecognitionLog = {
  full_name: string;
  confidence: number;
  is_unknown: boolean;
  bbox: { x1: number; y1: number; x2: number; y2: number };
  person_id?: number | null;
  person_code?: string;
  department?: string;
  title?: string;
  email?: string;
  phone?: string;
  mood?: string | null;
  liveness_score?: number | null;
  tracking_id?: number;
  is_enhanced?: boolean;
};

function drawPremiumBoundingBox(ctx: CanvasRenderingContext2D, m: RecognitionLog) {
  const isUnknown = m.is_unknown;
  const color = isUnknown ? "#f43f5e" : "#b4a5f5"; // Rose vs Neon Lavender
  const bgFill = isUnknown ? "rgba(244, 63, 94, 0.15)" : "rgba(180, 165, 245, 0.15)";
  
  const { x1, y1, x2, y2 } = m.bbox;
  const w = x2 - x1;
  const h = y2 - y1;
  const cornerLength = Math.max(10, Math.min(w, h) * 0.2);
  
  ctx.save();
  
  // Draw subtle background fill
  ctx.fillStyle = bgFill;
  ctx.fillRect(x1, y1, w, h);
  
  ctx.strokeStyle = color;
  ctx.lineWidth = Math.max(2, w * 0.015);
  ctx.lineCap = "round";
  ctx.lineJoin = "round";
  
  // Top-left
  ctx.beginPath();
  ctx.moveTo(x1, y1 + cornerLength);
  ctx.lineTo(x1, y1);
  ctx.lineTo(x1 + cornerLength, y1);
  ctx.stroke();
  
  // Top-right
  ctx.beginPath();
  ctx.moveTo(x2 - cornerLength, y1);
  ctx.lineTo(x2, y1);
  ctx.lineTo(x2, y1 + cornerLength);
  ctx.stroke();
  
  // Bottom-right
  ctx.beginPath();
  ctx.moveTo(x2, y2 - cornerLength);
  ctx.lineTo(x2, y2);
  ctx.lineTo(x2 - cornerLength, y2);
  ctx.stroke();
  
  // Bottom-left
  ctx.beginPath();
  ctx.moveTo(x1 + cornerLength, y2);
  ctx.lineTo(x1, y2);
  ctx.lineTo(x1, y2 - cornerLength);
  ctx.stroke();
  
  // Label
  const fontSize = Math.max(12, Math.floor(w * 0.08));
  ctx.font = `600 ${fontSize}px sans-serif`;
  const mood = m.mood ? ` · ${m.mood}` : "";
  const text = `${m.is_unknown ? "Unknown" : m.full_name} ${(m.confidence * 100).toFixed(1)}%${mood}`;
  const textWidth = ctx.measureText(text).width;
  const textHeight = fontSize;
  
  const padX = 8;
  const padY = 6;
  const labelW = textWidth + padX * 2;
  const labelH = textHeight + padY * 2;
  const labelY = y1 - labelH - 6;
  
  // Label background with gradient
  const grad = ctx.createLinearGradient(x1, labelY, x1 + labelW, labelY);
  grad.addColorStop(0, color);
  grad.addColorStop(1, isUnknown ? "#be123c" : "#8a63f2"); // Darker rose vs primary violet
  
  ctx.fillStyle = grad;
  ctx.beginPath();
  if (ctx.roundRect) {
    ctx.roundRect(x1, Math.max(0, labelY), labelW, labelH, [6, 6, 6, 6]);
  } else {
    ctx.fillRect(x1, Math.max(0, labelY), labelW, labelH);
  }
  ctx.fill();
  
  // Label text shadow
  ctx.shadowColor = "rgba(0,0,0,0.5)";
  ctx.shadowBlur = 4;
  ctx.shadowOffsetY = 1;
  ctx.fillStyle = "#ffffff";
  ctx.fillText(text, x1 + padX, Math.max(0, labelY) + textHeight + padY / 2 - 1);
  
  // Draw Tracking ID if present
  if (m.tracking_id !== undefined) {
    ctx.fillStyle = "rgba(0,0,0,0.6)";
    const trW = 40;
    const trH = 20;
    ctx.fillRect(x2 - trW, y2 - trH, trW, trH);
    ctx.fillStyle = "white";
    ctx.font = `500 ${Math.max(10, fontSize * 0.7)}px monospace`;
    ctx.fillText(`ID:${m.tracking_id}`, x2 - trW + 4, y2 - 6);
  }
  
  ctx.restore();
}

import { FaceTrackerCard } from "./ui/face-tracker-card";

export function WebcamModal() {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const overlayRef = useRef<HTMLCanvasElement>(null);
  const annotatedRef = useRef<HTMLImageElement>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const runningRef = useRef(false);
  const waitingRef = useRef(false);
  const [status, setStatus] = useState("Idle");
  const [logs, setLogs] = useState<RecognitionLog[]>([]);
  const [showAnnotated, setShowAnnotated] = useState(false);
  const [isCameraOn, setIsCameraOn] = useState(false);
  const [isLiveActive, setIsLiveActive] = useState(false);
  const [enableEnhancement, setEnableEnhancement] = useState(true);
  const [isOpen, setIsOpen] = useState(false);
  const [lowLightActive, setLowLightActive] = useState(false);
  const [enhancementActive, setEnhancementActive] = useState(false);

  const handleOpenChange = (open: boolean) => {
    setIsOpen(open);
    if (!open) {
      turnOffCamera();
    }
  };

  useEffect(() => {
    return () => {
      turnOffCamera();
    };
  }, []);

  const turnOnCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
      if (videoRef.current) videoRef.current.srcObject = stream;
      setIsCameraOn(true);
      setStatus("Camera active");
      setShowAnnotated(false);
      setLogs([]);
    } catch (err) {
      setStatus("Failed to access camera");
    }
  };

  const turnOffCamera = () => {
    stopLiveAI();
    const stream = videoRef.current?.srcObject;
    if (stream instanceof MediaStream) {
      stream.getTracks().forEach((t) => t.stop());
    }
    if (videoRef.current) videoRef.current.srcObject = null;
    setIsCameraOn(false);
    setStatus("Idle");
    setLogs([]);
    setShowAnnotated(false);
    setLowLightActive(false);
    setEnhancementActive(false);
  };

  const startLiveAI = () => {
    if (!isCameraOn) return;
    setIsLiveActive(true);
    
    const token = localStorage.getItem("visionid_token");
    // Pass enhancement flag via URL query param to WS
    const wsUrl = API_BASE.replace("http://", "ws://").replace("https://", "wss://") + 
                  `/recognition/ws?enhance=${enableEnhancement ? 'true' : 'false'}` + 
                  (token ? `&token=${token}` : "");
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;
    ws.onopen = () => setStatus("Connected — detecting faces...");
    ws.onclose = (ev) => { 
      setStatus(`Disconnected from Live AI (Code: ${ev.code})`); 
      setIsLiveActive(false); 
      setShowAnnotated(false); 
    };

    ws.onmessage = (ev) => {
      waitingRef.current = false;
      try {
        const msg = JSON.parse(ev.data);
        if (msg.type === "frame" && Array.isArray(msg.logs)) {
          setLogs(msg.logs);
          if (msg.meta) {
            setLowLightActive(Boolean(msg.meta.is_low_light));
            setEnhancementActive(Boolean(msg.meta.is_enhanced));
          }
          const known = msg.logs.filter((l: RecognitionLog) => !l.is_unknown);
          const unknown = msg.logs.filter((l: RecognitionLog) => l.is_unknown);
          setStatus(
            `Live — ${msg.logs.length} face(s) detected` +
            (known.length ? ` · ${known.length} recognized` : "") +
            (unknown.length ? ` · ${unknown.length} unknown` : "")
          );

          // Draw on overlay
          const v = videoRef.current;
          const canvas = overlayRef.current;
          if (v && canvas && v.videoWidth > 0) {
            const maxDim = 640;
            let w = v.videoWidth;
            let h = v.videoHeight;
            if (w > maxDim || h > maxDim) {
              const ratio = Math.min(maxDim / w, maxDim / h);
              w = w * ratio;
              h = h * ratio;
            }
            canvas.width = w;
            canvas.height = h;
            const ctx = canvas.getContext("2d");
            if (ctx) {
              ctx.clearRect(0, 0, w, h);
              ctx.lineWidth = Math.max(2, Math.floor(w / 200));
              ctx.font = `${Math.max(14, Math.floor(w / 40))}px sans-serif`;
              
              msg.logs.forEach((m: RecognitionLog) => {
                drawPremiumBoundingBox(ctx, m);
              });
            }
          }
        } else if (msg.type === "error") {
          setStatus(`Live Error: ${msg.message}`);
        }
      } catch {
        setStatus(`Live payload ${ev.data.length} bytes`);
      }
    };

    runningRef.current = true;

    const tick = () => {
      if (!runningRef.current) return;
      
      if (ws.readyState === WebSocket.OPEN) {
        const v = videoRef.current;
        const canvas = canvasRef.current;
        if (v && canvas && v.readyState >= 2 && v.videoWidth > 0 && !waitingRef.current) {
          const maxDim = 640;
          let w = v.videoWidth;
          let h = v.videoHeight;
          
          if (w > maxDim || h > maxDim) {
            const ratio = Math.min(maxDim / w, maxDim / h);
            w = w * ratio;
            h = h * ratio;
          }

          canvas.width = w;
          canvas.height = h;
          const ctx = canvas.getContext("2d");
          if (ctx) {
            ctx.drawImage(v, 0, 0, w, h);
            waitingRef.current = true;
            ws.send(canvas.toDataURL("image/jpeg", 0.7));
          }
        }
      }
      
      requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);
  };

  const stopLiveAI = () => {
    runningRef.current = false;
    setIsLiveActive(false);
    wsRef.current?.close();
    wsRef.current = null;
    setShowAnnotated(false);
    setStatus("Camera active");
  };

  const capturePhoto = async () => {
    if (!isCameraOn) return;
    if (isLiveActive) stopLiveAI();

    const v = videoRef.current;
    const canvas = canvasRef.current;
    if (!v || !canvas || v.readyState < 2 || v.videoWidth === 0) return;

    // Use full resolution for capture
    canvas.width = v.videoWidth;
    canvas.height = v.videoHeight;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    ctx.drawImage(v, 0, 0, canvas.width, canvas.height);

    setStatus("Analyzing captured photo...");
    
    canvas.toBlob(async (blob) => {
      if (!blob) return;
      const fd = new FormData();
      fd.append("image", blob, "capture.jpg");
      
      try {
        const res = await api.post("/recognition/image", fd);
        const results = Array.isArray(res.data) ? res.data : (res.data?.results || []);
        setLogs(results);
        
        ctx.lineWidth = Math.max(2, Math.floor(canvas.width / 400));
        ctx.font = `${Math.max(14, Math.floor(canvas.width / 40))}px sans-serif`;
        
        results.forEach((m: RecognitionLog) => {
          drawPremiumBoundingBox(ctx, m);
        });
        
        if (annotatedRef.current) {
          annotatedRef.current.src = canvas.toDataURL("image/jpeg", 0.9);
          setShowAnnotated(true);
        }
        
        const known = results.filter((l: RecognitionLog) => !l.is_unknown);
        const unknown = results.filter((l: RecognitionLog) => l.is_unknown);
        setStatus(
          `Captured — ${results.length} face(s) detected` +
          (known.length ? ` · ${known.length} recognized` : "") +
          (unknown.length ? ` · ${unknown.length} unknown` : "")
        );
      } catch (err) {
        setStatus("Error analyzing photo");
      }
    }, "image/jpeg", 0.95);
  };

  const knownCount = logs.filter((l) => !l.is_unknown).length;
  const unknownCount = logs.filter((l) => l.is_unknown).length;

  return (
    <Dialog open={isOpen} onOpenChange={handleOpenChange}>
      <DialogTrigger asChild>
        <Button variant="secondary" className="w-full bg-primary/20 text-accent border border-primary/20 hover:bg-primary/30">Open Webcam Studio</Button>
      </DialogTrigger>
      <DialogContent className="max-w-5xl overflow-hidden p-0 bg-[rgb(var(--bg))]/95 backdrop-blur-xl border-primary/20 shadow-glow-violet-lg">
        <div className="grid gap-0 md:grid-cols-[1fr_350px] min-h-[500px]">
          <div className="relative bg-black flex items-center justify-center p-4">
            {/* Raw camera feed always visible */}
            <video
              ref={videoRef}
              autoPlay
              playsInline
              className="aspect-video w-full rounded-lg bg-black object-cover shadow-2xl ring-1 ring-white/10"
            />
            {/* Overlay canvas for Live AI bounding boxes */}
            <canvas
              ref={overlayRef}
              className={`absolute inset-0 aspect-video w-full h-full rounded-lg object-contain pointer-events-none ${isLiveActive ? "block" : "hidden"} p-4`}
            />
            {/* Annotated frame from server for photo captures */}
            <img
              ref={annotatedRef}
              alt="Annotated webcam feed"
              className={`absolute inset-0 aspect-video w-full h-full rounded-lg bg-black object-contain ${showAnnotated && !isLiveActive ? "block" : "hidden"} p-4`}
            />
            <canvas ref={canvasRef} className="hidden" />
            {/* Face count badge */}
            {showAnnotated && logs.length > 0 && (
              <div className="absolute left-6 top-6 flex items-center gap-2 rounded-lg bg-black/80 px-4 py-2 text-sm font-medium text-white backdrop-blur shadow-lg ring-1 ring-white/20">
                <span className={`inline-block h-2.5 w-2.5 rounded-full ${isLiveActive ? "bg-green-500 animate-pulse" : "bg-blue-500"}`} />
                {logs.length} face{logs.length !== 1 ? "s" : ""} detected
              </div>
            )}
          </div>
          <div className="flex flex-col h-full bg-[rgb(var(--panel))]/40 border-l border-primary/20">
            <div className="p-4 border-b border-primary/20 glass-violet">
              <DialogTitle className="text-lg font-semibold tracking-tight text-white">Recognition Stream</DialogTitle>
              <div className="flex items-center justify-between mt-2">
                <p className="text-xs text-muted font-mono">{status}</p>
              </div>
              <div className="mt-3 flex flex-wrap gap-2">
                {lowLightActive && (
                  <span className="rounded-full bg-amber-500/20 text-amber-300 border border-amber-500/30 px-2 py-0.5 text-xs">
                    Low Light Detected
                  </span>
                )}
                {enhancementActive && (
                  <span className="rounded-full bg-blue-500/20 text-blue-300 border border-blue-500/30 px-2 py-0.5 text-xs">
                    Enhancement Active
                  </span>
                )}
              </div>
            </div>

            {/* Recognition results */}
            <div className="flex-1 min-h-0 overflow-y-auto p-4 space-y-3">
              <div className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-3 flex items-center justify-between">
                <span>Active Detections</span>
                <span className="bg-primary/10 text-primary px-2 py-0.5 rounded-full">{logs.length}</span>
              </div>
              <div className="flex flex-wrap gap-2 text-xs mb-3">
                <span className="rounded-full bg-emerald-500/15 text-emerald-300 border border-emerald-500/30 px-2 py-0.5">Known: {knownCount}</span>
                <span className="rounded-full bg-rose-500/15 text-rose-300 border border-rose-500/30 px-2 py-0.5">Unknown: {unknownCount}</span>
                <span className="rounded-full bg-primary/15 text-accent border border-primary/30 px-2 py-0.5">Total: {logs.length}</span>
              </div>
              {logs.length > 0 ? (
                <div className="space-y-3">
                  {logs.map((log, idx) => (
                    <FaceTrackerCard key={idx} match={log as any} />
                  ))}
                </div>
              ) : (
                <div className="h-40 flex flex-col items-center justify-center text-muted-foreground text-sm italic opacity-70">
                  <div className="w-12 h-12 rounded-full bg-muted flex items-center justify-center mb-3">
                    <span className="text-xl">👤</span>
                  </div>
                  No faces in view
                </div>
              )}
            </div>

            <div className="p-4 border-t border-primary/20 glass-violet flex flex-col gap-3 shrink-0">
              <div className="flex items-center gap-2 px-1 mb-1">
                <input 
                  type="checkbox" 
                  id="enhance" 
                  checked={enableEnhancement} 
                  onChange={(e) => setEnableEnhancement(e.target.checked)}
                  className="rounded border-primary/40 bg-black/40 text-primary focus:ring-primary"
                  disabled={isLiveActive}
                />
                <label htmlFor="enhance" className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70 text-white">
                  Enable Low-Light Enhancement
                </label>
              </div>
              
              {!isCameraOn ? (
                <Button className="w-full font-medium shadow-glow-violet bg-primary hover:bg-primary/90 text-white" onClick={turnOnCamera} size="lg">Turn On Camera</Button>
              ) : (
                <>
                  <div className="flex gap-2">
                    <Button className="flex-1 shadow-sm bg-primary/20 text-accent hover:bg-primary/30 border border-primary/30" variant="secondary" onClick={capturePhoto}>📸 Photo</Button>
                    {isLiveActive ? (
                      <Button className="flex-1 shadow-sm bg-rose-500/20 text-rose-300 hover:bg-rose-500/30 border border-rose-500/30" variant="destructive" onClick={stopLiveAI}>
                        <span className="w-2 h-2 rounded-full bg-rose-400 animate-pulse mr-2"></span>
                        Stop Live
                      </Button>
                    ) : (
                      <Button className="flex-1 shadow-glow-violet bg-primary hover:bg-primary/90 text-white" variant="default" onClick={startLiveAI}>▶️ Start Live AI</Button>
                    )}
                  </div>
                  <Button className="w-full text-muted hover:text-white hover:bg-white/5" variant="ghost" onClick={turnOffCamera}>Disconnect Camera</Button>
                </>
              )}
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
