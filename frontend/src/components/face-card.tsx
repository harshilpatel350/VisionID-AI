"use client";

import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

export function FaceCard({ person }: { person: any }) {
  return (
    <Card className="overflow-hidden">
      <CardContent className="flex items-center gap-4 p-0">
        <div className="h-20 w-20 rounded-2xl bg-white/5 p-2">
          <div className="grid h-full w-full place-items-center rounded-xl bg-indigo-500/15 text-indigo-200">
            {person.full_name?.charAt(0)}
          </div>
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <div className="truncate text-base font-semibold">{person.full_name}</div>
            {person.is_active ? <Badge>Active</Badge> : <Badge className="bg-rose-500/15">Inactive</Badge>}
          </div>
          <div className="mt-1 text-sm text-slate-400">{person.person_code}</div>
          <div className="mt-2 text-xs text-slate-500">{person.sample_count ?? 0} samples • {person.department ?? "No department"}</div>
        </div>
      </CardContent>
    </Card>
  );
}
