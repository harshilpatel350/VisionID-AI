"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { api } from "@/lib/api";
import { setAuth } from "@/lib/auth";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardTitle } from "@/components/ui/card";
import { ScanFace, Loader2 } from "lucide-react";
import { motion } from "framer-motion";

export default function LoginPage() {
  const router = useRouter();
  const [form, setForm] = useState({ username: "", password: "" });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const { data } = await api.post("/auth/login", form);
      const me = await api.get("/auth/me", {
        headers: { Authorization: `Bearer ${data.access_token}` },
      });
      setAuth(data.access_token, me.data);
      router.push("/dashboard");
    } catch (err: any) {
      setError(err?.response?.data?.detail ?? "Invalid username or password");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="grid min-h-screen place-items-center px-4 bg-transparent text-white relative">
      <div className="pointer-events-none fixed inset-0 bg-grid-fine bg-[length:42px_42px] opacity-[0.04]" />
      
      <motion.div 
        initial={{ opacity: 0, y: 20 }} 
        animate={{ opacity: 1, y: 0 }} 
        transition={{ duration: 0.5, ease: "easeOut" }}
        className="w-full max-w-md z-10"
      >
        <div className="flex justify-center mb-8">
          <div className="grid h-16 w-16 place-items-center rounded-3xl bg-primary/20 text-accent shadow-glow-violet">
            <ScanFace className="h-8 w-8" />
          </div>
        </div>
        
        <Card className="glass-violet overflow-hidden border-primary/20">
          <CardTitle className="px-6 pt-6 text-xl font-bold tracking-tight text-white text-center">
            Welcome to VisionID
          </CardTitle>
          <div className="text-center text-sm text-muted mt-1">Sign in to your premium account</div>
          
          <CardContent className="mt-6 space-y-4 px-6 pb-6">
            <form onSubmit={submit} className="space-y-4">
              <div className="space-y-3">
                <Input 
                  placeholder="Username" 
                  value={form.username} 
                  onChange={(e) => setForm({ ...form, username: e.target.value })} 
                  className="bg-black/20 border-white/10 focus-visible:ring-primary h-11"
                />
                <Input 
                  placeholder="Password" 
                  type="password" 
                  value={form.password} 
                  onChange={(e) => setForm({ ...form, password: e.target.value })} 
                  className="bg-black/20 border-white/10 focus-visible:ring-primary h-11"
                />
              </div>
              
              {error ? (
                <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} className="rounded-xl border border-rose-500/30 bg-rose-500/10 p-3 text-sm text-rose-200">
                  {error}
                </motion.div>
              ) : null}
              
              <Button 
                className="w-full h-11 bg-primary hover:bg-primary/90 text-white shadow-glow-violet transition-all" 
                disabled={loading}
              >
                {loading ? <Loader2 className="h-5 w-5 animate-spin" /> : "Sign In"}
              </Button>
            </form>
            <div className="text-center text-sm text-muted pt-2">
              Don't have an account? <Link href="/register" className="text-accent hover:text-white transition-colors">Create one</Link>
            </div>
          </CardContent>
        </Card>
      </motion.div>
    </main>
  );
}
