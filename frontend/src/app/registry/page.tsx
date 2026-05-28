"use client";

import { useEffect, useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { AppShell } from "@/components/app-shell";
import { Card, CardContent, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { FaceCard } from "@/components/face-card";
import { Badge } from "@/components/ui/badge";

export default function RegistryPage() {
  const persons = useQuery({ queryKey: ["persons"], queryFn: async () => (await api.get("/faces/persons")).data });
  const [form, setForm] = useState({ full_name: "", email: "", phone: "", department: "", title: "", age: "", gender: "", tags: "", notes: "" });
  const [files, setFiles] = useState<FileList | null>(null);
  const [message, setMessage] = useState("");
  const [quality, setQuality] = useState<any | null>(null);
  const [duplicateHit, setDuplicateHit] = useState<any | null>(null);
  const [qualityLoading, setQualityLoading] = useState(false);
  const [duplicateLoading, setDuplicateLoading] = useState(false);
  
  // Webcam state
  const videoRef = useRef<HTMLVideoElement>(null);
  const [isCameraOn, setIsCameraOn] = useState(false);
  const [capturedImage, setCapturedImage] = useState<Blob | null>(null);
  const [capturedUrl, setCapturedUrl] = useState<string | null>(null);

  useEffect(() => {
    return () => {
      stopCamera();
    };
  }, []);

  const toggleCamera = async () => {
    if (isCameraOn) {
      stopCamera();
    } else {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ video: true });
        if (videoRef.current) videoRef.current.srcObject = stream;
        setIsCameraOn(true);
        setCapturedImage(null);
        if (capturedUrl) URL.revokeObjectURL(capturedUrl);
        setCapturedUrl(null);
      } catch (err) {
        console.error("Camera access denied", err);
      }
    }
  };

  const analyzeSample = async (file: Blob) => {
    setQualityLoading(true);
    setDuplicateLoading(true);
    setQuality(null);
    setDuplicateHit(null);
    try {
      const fd1 = new FormData();
      fd1.append("image", file, "sample.jpg");
      const res = await api.post("/faces/quality", fd1);
      setQuality(res.data?.data ?? res.data);
    } catch (err) {
      setQuality(null);
    } finally {
      setQualityLoading(false);
    }

    try {
      const fd2 = new FormData();
      fd2.append("image", file, "sample.jpg");
      const res = await api.post("/faces/duplicate-check", fd2);
      setDuplicateHit(res.data?.data ?? res.data);
    } catch (err) {
      setDuplicateHit(null);
    } finally {
      setDuplicateLoading(false);
    }
  };

  const stopCamera = () => {
    const stream = videoRef.current?.srcObject;
    if (stream instanceof MediaStream) {
      stream.getTracks().forEach((t) => t.stop());
    }
    if (videoRef.current) videoRef.current.srcObject = null;
    setIsCameraOn(false);
  };

  const capturePhoto = () => {
    const v = videoRef.current;
    if (!v || v.readyState < 2 || v.videoWidth === 0) return;
    
    const canvas = document.createElement("canvas");
    canvas.width = v.videoWidth;
    canvas.height = v.videoHeight;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    ctx.drawImage(v, 0, 0, canvas.width, canvas.height);
    
    canvas.toBlob((blob) => {
      if (!blob) return;
      setCapturedImage(blob);
      setCapturedUrl(URL.createObjectURL(blob));
      stopCamera();
      analyzeSample(blob);
    }, "image/jpeg", 0.95);
  };

  const clearCapture = () => {
    setCapturedImage(null);
    if (capturedUrl) URL.revokeObjectURL(capturedUrl);
    setCapturedUrl(null);
    setQuality(null);
    setDuplicateHit(null);
  };

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setMessage("");
    
    if (!form.full_name) {
      setMessage("Full name is required.");
      return;
    }
    if (!files?.length && !capturedImage) {
      setMessage("Please upload an image or capture a photo.");
      return;
    }

    const fd = new FormData();
    Object.entries(form).forEach(([k, v]) => {
      if (v.trim() !== "") fd.append(k, v);
    });
    
    if (files) Array.from(files).forEach((f) => fd.append("images", f));
    if (capturedImage) fd.append("images", capturedImage, "capture.jpg");
    
    try {
      await api.post("/faces/persons", fd);
      setMessage("Person registered successfully");
      setForm({ full_name: "", email: "", phone: "", department: "", title: "", age: "", gender: "", tags: "", notes: "" });
      setFiles(null);
      clearCapture();
      persons.refetch();
    } catch (err: any) {
      setMessage("Error: " + (err.response?.data?.detail || err.message));
    }
  };

  const deletePerson = async (id: number) => {
    try {
      await api.delete(`/faces/persons/${id}`);
      persons.refetch();
    } catch (err: any) {
      alert("Failed to delete: " + (err.response?.data?.detail || err.message));
    }
  };

  const exportRegistry = async (format: "csv" | "xlsx") => {
    const mime = format === "csv" ? "text/csv" : "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet";
    const res = await api.get(`/exports/persons.${format}`, { responseType: "blob" });
    const blob = new Blob([res.data], { type: mime });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement("a");
    const stamp = new Date().toISOString().slice(0, 10);
    link.href = url;
    link.download = `persons_${stamp}.${format}`;
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  };

  return (
    <AppShell>
      <div className="grid gap-6 xl:grid-cols-[450px_1fr]">
        <Card className="glass-violet border-primary/20">
          <CardTitle className="text-white">Register Person</CardTitle>
          <CardContent className="mt-4">
            <form className="space-y-4" onSubmit={submit}>
              <div className="space-y-2">
                <Input placeholder="Full name *" required value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} className="bg-black/20 border-white/10 focus-visible:ring-primary" />
                <div className="grid grid-cols-2 gap-2">
                  <Input placeholder="Email (optional)" type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} className="bg-black/20 border-white/10 focus-visible:ring-primary" />
                  <Input placeholder="Phone (optional)" value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} className="bg-black/20 border-white/10 focus-visible:ring-primary" />
                </div>
                <div className="grid grid-cols-2 gap-2">
                  <Input placeholder="Department" value={form.department} onChange={(e) => setForm({ ...form, department: e.target.value })} className="bg-black/20 border-white/10 focus-visible:ring-primary" />
                  <Input placeholder="Title" value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} className="bg-black/20 border-white/10 focus-visible:ring-primary" />
                </div>
                <div className="grid grid-cols-3 gap-2">
                  <Input placeholder="Age" type="number" value={form.age} onChange={(e) => setForm({ ...form, age: e.target.value })} className="bg-black/20 border-white/10 focus-visible:ring-primary" />
                  <select 
                    className="flex h-9 w-full rounded-md border border-white/10 bg-black/20 px-3 py-1 text-sm shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-primary disabled:cursor-not-allowed disabled:opacity-50 text-white"
                    value={form.gender} 
                    onChange={(e) => setForm({ ...form, gender: e.target.value })}
                  >
                    <option value="" disabled className="bg-[rgb(var(--panel))] text-white">Gender</option>
                    <option value="male" className="bg-[rgb(var(--panel))] text-white">Male</option>
                    <option value="female" className="bg-[rgb(var(--panel))] text-white">Female</option>
                    <option value="other" className="bg-[rgb(var(--panel))] text-white">Other</option>
                  </select>
                  <Input placeholder="Tags (VIP, Staff...)" value={form.tags} onChange={(e) => setForm({ ...form, tags: e.target.value })} className="bg-black/20 border-white/10 focus-visible:ring-primary" />
                </div>
                <Input placeholder="Notes (optional)" value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} className="bg-black/20 border-white/10 focus-visible:ring-primary" />
              </div>

              <div className="space-y-2">
                <div className="flex gap-2">
                  <Button type="button" variant={isCameraOn ? "destructive" : "secondary"} className={`flex-1 ${isCameraOn ? 'bg-rose-500/20 text-rose-300 hover:bg-rose-500/30 border border-rose-500/30' : 'bg-primary/20 text-accent hover:bg-primary/30 border border-primary/30'}`} onClick={toggleCamera}>
                    {isCameraOn ? "Stop Camera" : "📸 Use Camera"}
                  </Button>
                  <div className="flex-1">
                    <Input
                      type="file"
                      accept="image/*"
                      multiple
                      onChange={(e) => {
                        setFiles(e.target.files);
                        const first = e.target.files?.[0];
                        if (first) analyzeSample(first);
                      }}
                      className="cursor-pointer bg-black/20 border-white/10"
                    />
                  </div>
                </div>

                <div className={`relative overflow-hidden rounded-xl bg-black border border-primary/20 ${isCameraOn ? "block" : "hidden"}`}>
                  <video ref={videoRef} autoPlay playsInline className="aspect-video w-full object-cover" />
                  <div className="absolute inset-x-0 bottom-0 p-3 bg-gradient-to-t from-black/80 to-transparent flex justify-center">
                    <Button type="button" variant="default" className="rounded-full shadow-glow-violet bg-primary hover:bg-primary/90 text-white" onClick={capturePhoto}>
                      Snap Photo
                    </Button>
                  </div>
                </div>

                {capturedUrl && !isCameraOn && (
                  <div className="relative group overflow-hidden rounded-xl border border-primary/20">
                    <img src={capturedUrl} alt="Captured" className="aspect-video w-full object-cover" />
                    <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                      <Button type="button" variant="destructive" onClick={clearCapture}>Remove Photo</Button>
                    </div>
                  </div>
                )}

                <div className="grid gap-3">
                  <div className="rounded-xl border border-primary/20 bg-black/30 p-3">
                    <div className="flex items-center justify-between mb-2">
                      <div className="text-xs uppercase tracking-wider text-muted">Face Quality</div>
                      {qualityLoading && <Badge className="bg-primary/20 text-accent border border-primary/30">Scanning...</Badge>}
                    </div>
                    {quality ? (
                      <div className="grid grid-cols-3 gap-2 text-xs">
                        <div className="flex flex-col">
                          <span className="text-muted">Overall</span>
                          <span className={`font-semibold ${quality.is_valid ? "text-emerald-300" : "text-rose-300"}`}>{Math.round(quality.overall * 100)}%</span>
                        </div>
                        <div className="flex flex-col">
                          <span className="text-muted">Blur</span>
                          <span className="font-semibold text-white">{Math.round(quality.blur * 100)}%</span>
                        </div>
                        <div className="flex flex-col">
                          <span className="text-muted">Brightness</span>
                          <span className="font-semibold text-white">{Math.round(quality.brightness * 100)}%</span>
                        </div>
                        <div className="flex flex-col">
                          <span className="text-muted">Size</span>
                          <span className="font-semibold text-white">{Math.round(quality.size_score * 100)}%</span>
                        </div>
                        <div className="flex flex-col">
                          <span className="text-muted">Pose</span>
                          <span className="font-semibold text-white">{Math.round(quality.pose_score * 100)}%</span>
                        </div>
                      </div>
                    ) : (
                      <div className="text-xs text-muted">Upload or capture a face to evaluate quality.</div>
                    )}
                  </div>

                  <div className="rounded-xl border border-primary/20 bg-black/30 p-3">
                    <div className="flex items-center justify-between mb-2">
                      <div className="text-xs uppercase tracking-wider text-muted">Duplicate Check</div>
                      {duplicateLoading && <Badge className="bg-primary/20 text-accent border border-primary/30">Searching...</Badge>}
                    </div>
                    {duplicateHit ? (
                      <div className="text-xs text-rose-300">
                        Possible match: <span className="font-semibold text-white">{duplicateHit.full_name}</span> ({duplicateHit.person_code}) · {(duplicateHit.similarity * 100).toFixed(1)}%
                      </div>
                    ) : capturedImage || files ? (
                      <div className="text-xs text-emerald-300">No close duplicates detected.</div>
                    ) : (
                      <div className="text-xs text-muted">Upload or capture a face to check duplicates.</div>
                    )}
                  </div>
                </div>
              </div>

              <Button className="w-full bg-primary hover:bg-primary/90 text-white shadow-glow-violet" type="submit">Register Face</Button>
              {message ? (
                <div className={`text-sm ${message.includes("Error") ? "text-red-400" : "text-emerald-300"}`}>
                  {message}
                </div>
              ) : null}
            </form>
          </CardContent>
        </Card>

        <Card className="glass-violet border-primary/20">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div className="flex flex-col">
              <CardTitle className="text-white">Face Registry</CardTitle>
              <div className="text-xs text-muted">Total people: {persons.data?._meta?.total ?? persons.data?.length ?? 0}</div>
            </div>
            <div className="flex gap-2">
              <Button variant="outline" className="border-primary/20 text-accent" onClick={() => exportRegistry("csv")}>Export CSV</Button>
              <Button variant="outline" className="border-primary/20 text-accent" onClick={() => exportRegistry("xlsx")}>Export XLSX</Button>
            </div>
          </div>
          <CardContent className="mt-4 grid gap-4 md:grid-cols-2 xl:grid-cols-2">
            {(persons.data ?? []).map((person: any) => (
              <FaceCard key={person.id} person={person} onDelete={deletePerson} />
            ))}
          </CardContent>
        </Card>
      </div>
    </AppShell>
  );
}
