"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardTitle } from "@/components/ui/card";
import { Sparkles, Loader2 } from "lucide-react";
import { motion } from "framer-motion";

export default function RegisterPage() {
  const router = useRouter();
  const [form, setForm] = useState({ full_name: "", username: "", password: "", confirmPassword: "" });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (form.password !== form.confirmPassword) {
      setError("Passwords do not match");
      return;
    }
    setLoading(true);
    setError("");
    try {
      await api.post("/auth/register", {
        full_name: form.full_name,
        username: form.username,
        password: form.password
      });
      router.push("/login");
    } catch (err: any) {
      setError(err?.response?.data?.detail ?? "Failed to create account");
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
            <Sparkles className="h-8 w-8" />
          </div>
        </div>
        
        <Card className="glass-violet overflow-hidden border-primary/20">
          <CardTitle className="px-6 pt-6 text-xl font-bold tracking-tight text-white text-center">
            Create an Account
          </CardTitle>
          <div className="text-center text-sm text-muted mt-1">Join the VisionID intelligence platform</div>
          
          <CardContent className="mt-6 space-y-4 px-6 pb-6">
            <form onSubmit={submit} className="space-y-4">
              <div className="space-y-3">
                <Input 
                  placeholder="Full Name" 
                  value={form.full_name} 
                  onChange={(e) => setForm({ ...form, full_name: e.target.value })} 
                  className="bg-black/20 border-white/10 focus-visible:ring-primary h-11"
                  required
                />
                <Input 
                  placeholder="Username" 
                  value={form.username} 
                  onChange={(e) => setForm({ ...form, username: e.target.value })} 
                  className="bg-black/20 border-white/10 focus-visible:ring-primary h-11"
                  required
                />
                <Input 
                  placeholder="Password" 
                  type="password" 
                  value={form.password} 
                  onChange={(e) => setForm({ ...form, password: e.target.value })} 
                  className="bg-black/20 border-white/10 focus-visible:ring-primary h-11"
                  required
                />
                <Input 
                  placeholder="Confirm Password" 
                  type="password" 
                  value={form.confirmPassword} 
                  onChange={(e) => setForm({ ...form, confirmPassword: e.target.value })} 
                  className="bg-black/20 border-white/10 focus-visible:ring-primary h-11"
                  required
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
                {loading ? <Loader2 className="h-5 w-5 animate-spin" /> : "Sign Up"}
              </Button>
            </form>
            <div className="text-center text-sm text-muted pt-2">
              Already have an account? <Link href="/login" className="text-accent hover:text-white transition-colors">Sign in</Link>
            </div>
          </CardContent>
        </Card>
      </motion.div>
    </main>
  );
}
