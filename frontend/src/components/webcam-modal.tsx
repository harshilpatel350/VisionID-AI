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
  person_code?: string;
  department?: string;
  title?: string;
  email?: string;
  phone?: string;
};

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
  };

  const startLiveAI = () => {
    if (!isCameraOn) return;
    setIsLiveActive(true);
    
    const wsUrl = API_BASE.replace("http://", "ws://").replace("https://", "wss://") + "/recognition/ws";
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;
    ws.onopen = () => setStatus("Connected — detecting faces...");
    ws.onclose = () => { 
      setStatus("Disconnected from Live AI"); 
      setIsLiveActive(false); 
      setShowAnnotated(false); 
    };

    ws.onmessage = (ev) => {
      waitingRef.current = false;
      try {
        const msg = JSON.parse(ev.data);
        if (msg.type === "frame" && Array.isArray(msg.logs)) {
          setLogs(msg.logs);
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
                const color = m.is_unknown ? "#f97316" : "#10b981";
                ctx.strokeStyle = color;
                ctx.fillStyle = color;
                const { x1, y1, x2, y2 } = m.bbox;
                ctx.strokeRect(x1, y1, x2 - x1, y2 - y1);
                
                const text = `${m.full_name} ${(m.confidence * 100).toFixed(1)}%`;
                const textWidth = ctx.measureText(text).width;
                const textHeight = parseInt(ctx.font, 10);
                
                ctx.fillRect(x1, y1 - textHeight - 4, textWidth + 8, textHeight + 4);
                ctx.fillStyle = "#ffffff";
                ctx.fillText(text, x1 + 4, y1 - 4);
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
        const res = await api.post("/recognition/image", fd, {
          headers: { "Content-Type": "multipart/form-data" }
        });
        const results = res.data.results || [];
        setLogs(results);
        
        // Draw bounding boxes natively
        ctx.lineWidth = Math.max(2, Math.floor(canvas.width / 400));
        ctx.font = `${Math.max(14, Math.floor(canvas.width / 40))}px sans-serif`;
        
        results.forEach((m: RecognitionLog) => {
          const color = m.is_unknown ? "#f97316" : "#10b981"; // orange-500 / emerald-500
          ctx.strokeStyle = color;
          ctx.fillStyle = color;
          
          const { x1, y1, x2, y2 } = m.bbox;
          ctx.strokeRect(x1, y1, x2 - x1, y2 - y1);
          
          const text = `${m.full_name} ${(m.confidence * 100).toFixed(1)}%`;
          const textWidth = ctx.measureText(text).width;
          const textHeight = parseInt(ctx.font, 10);
          
          ctx.fillRect(x1, y1 - textHeight - 4, textWidth + 8, textHeight + 4);
          
          ctx.fillStyle = "#ffffff";
          ctx.fillText(text, x1 + 4, y1 - 4);
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

  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button variant="secondary">Open Webcam Studio</Button>
      </DialogTrigger>
      <DialogContent className="max-w-5xl">
        <DialogTitle className="sr-only">Webcam Recognition Studio</DialogTitle>
        <div className="grid gap-4 md:grid-cols-[1fr_320px]">
          <div className="relative">
            {/* Raw camera feed always visible */}
            <video
              ref={videoRef}
              autoPlay
              playsInline
              className="aspect-video w-full rounded-2xl bg-black object-contain"
            />
            {/* Overlay canvas for Live AI bounding boxes */}
            <canvas
              ref={overlayRef}
              className={`absolute inset-0 aspect-video w-full h-full rounded-2xl object-contain pointer-events-none ${isLiveActive ? "block" : "hidden"}`}
            />
            {/* Annotated frame from server for photo captures */}
            <img
              ref={annotatedRef}
              alt="Annotated webcam feed"
              className={`absolute inset-0 aspect-video w-full h-full rounded-2xl bg-black object-contain ${showAnnotated && !isLiveActive ? "block" : "hidden"}`}
            />
            <canvas ref={canvasRef} className="hidden" />
            {/* Face count badge */}
            {showAnnotated && logs.length > 0 && (
              <div className="absolute left-3 top-3 flex items-center gap-2 rounded-xl bg-black/70 px-3 py-1.5 text-xs font-medium text-white backdrop-blur">
                <span className={`inline-block h-2 w-2 rounded-full ${isLiveActive ? "bg-emerald-400 animate-pulse" : "bg-sky-400"}`} />
                {logs.length} face{logs.length !== 1 ? "s" : ""} detected
              </div>
            )}
          </div>
          <div className="space-y-4 flex flex-col h-full">
            <div className="rounded-2xl border border-white/10 bg-white/5 p-4 text-sm text-slate-300 h-[72px] shrink-0 overflow-hidden">
              <div className="mb-1 text-xs font-semibold uppercase tracking-wider text-slate-500">Status</div>
              <span className="text-white line-clamp-1">{status}</span>
            </div>

            {/* Recognition results - fixed height or flexible but contained */}
            <div className="flex-1 min-h-0 overflow-y-auto rounded-2xl border border-white/10 bg-white/5 p-4 space-y-2">
              <div className="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-2">Detections</div>
              {logs.length > 0 ? (
                <div className="space-y-2">
                  {logs.map((log, idx) => (
                    <div
                      key={idx}
                      className={`flex flex-col gap-1 rounded-xl px-3 py-2 text-sm ${
                        log.is_unknown
                          ? "border border-orange-500/20 bg-orange-500/10 text-orange-200"
                          : "border border-emerald-500/20 bg-emerald-500/10 text-emerald-200"
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-medium">{log.full_name}</span>
                        <span className="text-xs opacity-75">{(log.confidence * 100).toFixed(1)}%</span>
                      </div>
                      {!log.is_unknown && (
                        <div className="mt-1 flex flex-col gap-0.5 text-xs opacity-80">
                          {log.person_code && <div><span className="font-semibold">ID:</span> {log.person_code}</div>}
                          {log.title && <div><span className="font-semibold">Title:</span> {log.title}</div>}
                          {log.department && <div><span className="font-semibold">Dept:</span> {log.department}</div>}
                          {log.email && <div><span className="font-semibold">Email:</span> {log.email}</div>}
                          {log.phone && <div><span className="font-semibold">Phone:</span> {log.phone}</div>}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <div className="h-full flex items-center justify-center text-slate-500 text-xs italic">
                  No faces detected
                </div>
              )}
            </div>

            <div className="flex flex-col gap-2 mt-auto shrink-0">
              {!isCameraOn ? (
                <Button className="w-full" onClick={turnOnCamera}>Turn On Camera</Button>
              ) : (
                <>
                  <div className="flex gap-2">
                    <Button className="flex-1" variant="secondary" onClick={capturePhoto}>📸 Capture</Button>
                    {isLiveActive ? (
                      <Button className="flex-1" variant="destructive" onClick={stopLiveAI}>⏹ Stop Live</Button>
                    ) : (
                      <Button className="flex-1" variant="default" onClick={startLiveAI}>▶️ Live AI</Button>
                    )}
                  </div>
                  <Button className="w-full" variant="outline" onClick={turnOffCamera}>Turn Off Camera</Button>
                </>
              )}
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
