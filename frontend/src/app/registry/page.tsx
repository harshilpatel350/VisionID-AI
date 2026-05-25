"use client";

import { useEffect, useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { AppShell } from "@/components/app-shell";
import { Card, CardContent, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { FaceCard } from "@/components/face-card";

export default function RegistryPage() {
  const persons = useQuery({ queryKey: ["persons"], queryFn: async () => (await api.get("/faces/persons")).data });
  const [form, setForm] = useState({ full_name: "", email: "", phone: "", department: "", title: "", notes: "" });
  const [files, setFiles] = useState<FileList | null>(null);
  const [message, setMessage] = useState("");
  
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
    }, "image/jpeg", 0.95);
  };

  const clearCapture = () => {
    setCapturedImage(null);
    if (capturedUrl) URL.revokeObjectURL(capturedUrl);
    setCapturedUrl(null);
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
      setForm({ full_name: "", email: "", phone: "", department: "", title: "", notes: "" });
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

  return (
    <AppShell>
      <div className="grid gap-6 xl:grid-cols-[420px_1fr]">
        <Card>
          <CardTitle>Add Person</CardTitle>
          <CardContent className="mt-4">
            <form className="space-y-4" onSubmit={submit}>
              <div className="space-y-2">
                <Input placeholder="Full name *" required value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} />
                <Input placeholder="Email (optional)" type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
                <Input placeholder="Phone (optional)" value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} />
                <Input placeholder="Department (optional)" value={form.department} onChange={(e) => setForm({ ...form, department: e.target.value })} />
                <Input placeholder="Title (optional)" value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} />
                <Input placeholder="Notes (optional)" value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} />
              </div>

              <div className="space-y-2">
                <div className="flex gap-2">
                  <Button type="button" variant={isCameraOn ? "destructive" : "secondary"} className="flex-1" onClick={toggleCamera}>
                    {isCameraOn ? "Stop Camera" : "📸 Use Camera"}
                  </Button>
                  <div className="flex-1">
                    <Input type="file" accept="image/*" multiple onChange={(e) => setFiles(e.target.files)} className="cursor-pointer" />
                  </div>
                </div>

                <div className={`relative overflow-hidden rounded-xl bg-black border border-white/10 ${isCameraOn ? "block" : "hidden"}`}>
                  <video ref={videoRef} autoPlay playsInline className="aspect-video w-full object-cover" />
                  <div className="absolute inset-x-0 bottom-0 p-3 bg-gradient-to-t from-black/80 to-transparent flex justify-center">
                    <Button type="button" variant="default" className="rounded-full shadow-lg" onClick={capturePhoto}>
                      Snap Photo
                    </Button>
                  </div>
                </div>

                {capturedUrl && !isCameraOn && (
                  <div className="relative group overflow-hidden rounded-xl border border-white/10">
                    <img src={capturedUrl} alt="Captured" className="aspect-video w-full object-cover" />
                    <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                      <Button type="button" variant="destructive" onClick={clearCapture}>Remove Photo</Button>
                    </div>
                  </div>
                )}
              </div>

              <Button className="w-full" type="submit">Register Face</Button>
              {message ? (
                <div className={`text-sm ${message.includes("Error") ? "text-red-400" : "text-emerald-300"}`}>
                  {message}
                </div>
              ) : null}
            </form>
          </CardContent>
        </Card>

        <Card>
          <CardTitle>Face Registry</CardTitle>
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
