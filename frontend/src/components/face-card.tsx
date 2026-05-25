"use client";

import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Trash2 } from "lucide-react";
import { motion } from "framer-motion";

export function FaceCard({ person, onDelete }: { person: any, onDelete?: (id: number) => void }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 15 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.9 }}
      whileHover={{ scale: 1.02 }}
      transition={{ type: "spring", stiffness: 400, damping: 25 }}
    >
      <Card className="overflow-hidden group">
        <CardContent className="flex items-center gap-4 p-0">
          <div className="h-20 w-20 rounded-2xl bg-white/5 p-2 shrink-0">
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
          {onDelete && (
            <div className="pr-4 opacity-0 group-hover:opacity-100 transition-opacity">
              <Button 
                variant="destructive" 
                size="sm" 
                className="h-8 w-8 rounded-lg p-0"
                onClick={() => {
                  if (confirm(`Delete ${person.full_name}?`)) {
                    onDelete(person.id);
                  }
                }}
              >
                <Trash2 className="h-4 w-4" />
              </Button>
            </div>
          )}
        </CardContent>
      </Card>
    </motion.div>
  );
}
