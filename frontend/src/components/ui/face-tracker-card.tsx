import React from 'react';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { MoodChip } from './mood-chip';
import { UserX, UserCheck, ShieldAlert, Activity } from 'lucide-react';
import { cn } from '@/lib/utils';

export interface TrackerMatch {
  person_id: number | null;
  full_name: string;
  is_unknown: boolean;
  confidence: number;
  mood?: string | null;
  liveness_score?: number | null;
  tracking_id?: number;
  is_enhanced?: boolean;
}

interface FaceTrackerCardProps {
  match: TrackerMatch;
  className?: string;
}

export function FaceTrackerCard({ match, className }: FaceTrackerCardProps) {
  const isUnknown = match.is_unknown || !match.person_id;
  
  return (
    <Card className={cn(
      "overflow-hidden transition-all duration-300 border-l-4",
      isUnknown ? "border-l-red-500 bg-red-500/5" : "border-l-green-500 bg-card",
      className
    )}>
      <div className="p-3">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            {isUnknown ? (
              <div className="p-1.5 bg-red-500/20 text-red-500 rounded-md">
                <UserX size={16} />
              </div>
            ) : (
              <div className="p-1.5 bg-green-500/20 text-green-500 rounded-md">
                <UserCheck size={16} />
              </div>
            )}
            <div>
              <h4 className="font-semibold text-sm leading-none mb-1 text-foreground">
                {isUnknown ? "Unknown Face" : match.full_name}
              </h4>
              <div className="flex items-center gap-2 text-xs text-muted-foreground">
                <span>{(match.confidence * 100).toFixed(1)}% match</span>
                {match.tracking_id !== undefined && (
                  <span className="opacity-50">ID: {match.tracking_id}</span>
                )}
              </div>
            </div>
          </div>
          
          <Badge className={cn(isUnknown ? "bg-red-500/20 text-red-300 border-red-500/40 animate-pulse" : "bg-primary/20 text-accent border border-primary/30")}>
            {isUnknown ? "ALERT" : "KNOWN"}
          </Badge>
        </div>
        
        <div className="flex flex-wrap gap-2 mt-3">
          {match.mood && <MoodChip mood={match.mood} />}
          
          {match.liveness_score !== null && match.liveness_score !== undefined && (
            <Badge className="flex items-center gap-1 font-normal border-transparent bg-black/45 text-white">
              <Activity size={12} className={match.liveness_score > 0.5 ? "text-green-500" : "text-red-500"} />
              Liveness: {(match.liveness_score * 100).toFixed(0)}%
            </Badge>
          )}
          
          {match.is_enhanced && (
            <Badge className="flex items-center gap-1 font-normal border-transparent bg-blue-500/20 text-blue-400">
              Enhanced
            </Badge>
          )}
        </div>
      </div>
    </Card>
  );
}
