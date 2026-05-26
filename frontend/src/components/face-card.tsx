"use client";

import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Trash2 } from "lucide-react";
import { motion } from "framer-motion";

import { API_BASE } from "@/lib/api";

export function FaceCard({ person, onDelete }: { person: any, onDelete?: (id: number) => void }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 15 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.9 }}
      whileHover={{ scale: 1.02 }}
      transition={{ type: "spring", stiffness: 400, damping: 25 }}
    >
      <Card className="overflow-hidden group h-full glass-violet border-primary/20 hover:border-primary/40 hover:shadow-glow-violet transition-all duration-300">
        <CardContent className="flex items-center gap-4 p-4">
          <div className="h-20 w-20 rounded-2xl bg-black/20 p-1 shrink-0 overflow-hidden relative">
            {person.primary_image_path ? (
              <img src={`${API_BASE}/${person.primary_image_path}`} alt={person.full_name} className="h-full w-full object-cover rounded-xl" />
            ) : (
              <div className="grid h-full w-full place-items-center rounded-xl bg-primary/20 text-accent text-xl font-bold">
                {person.full_name?.charAt(0)}
              </div>
            )}
          </div>
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2">
              <div className="truncate text-base font-semibold text-white">{person.full_name}</div>
              {person.is_active ? <Badge className="bg-emerald-500/15 text-emerald-300 border-none">Active</Badge> : <Badge className="bg-rose-500/15 text-rose-300 border-none">Inactive</Badge>}
            </div>
            <div className="mt-1 text-sm text-muted flex items-center gap-2">
              <span>{person.person_code}</span>
              {person.department && <span>• {person.department}</span>}
              {person.title && <span>• {person.title}</span>}
            </div>
            
            <div className="flex flex-wrap gap-1 mt-2">
              {person.age && <Badge className="text-[10px] px-1.5 py-0">Age: {person.age}</Badge>}
              {person.gender && <Badge className="text-[10px] px-1.5 py-0 capitalize">{person.gender}</Badge>}
              {person.tags && person.tags.split(',').map((t: string) => <Badge key={t} className="text-[10px] px-1.5 py-0 bg-primary/10 text-primary">{t.trim()}</Badge>)}
            </div>
            
            <div className="mt-2 text-xs text-primary">{person.sample_count ?? 0} samples registered</div>
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
