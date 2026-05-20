"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { api } from "@/lib/api";
import { setAuth } from "@/lib/auth";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardTitle } from "@/components/ui/card";

export default function LoginPage() {
  const router = useRouter();
  const [form, setForm] = useState({ email: "", password: "" });
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
      setError(err?.response?.data?.detail ?? "Something went wrong");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="grid min-h-screen place-items-center px-4">
      <Card className="w-full max-w-md">
        <CardTitle>Welcome back</CardTitle>
        <CardContent className="mt-4 space-y-4">
          <form onSubmit={submit} className="space-y-3">
            <Input placeholder="Email" type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
            <Input placeholder="Password" type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} />
            {error ? <div className="rounded-xl border border-rose-500/20 bg-rose-500/10 p-3 text-sm text-rose-200">{error}</div> : null}
            <Button className="w-full" disabled={loading}>{loading ? "Signing in..." : "Login"}</Button>
          </form>
          <div className="text-sm text-slate-400">
            No account? <Link href="/register" className="text-indigo-300">Create one</Link>
          </div>
        </CardContent>
      </Card>
    </main>
  );
}
