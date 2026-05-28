import React from 'react';
import { Smile, Frown, Meh, AlertCircle, HelpCircle } from 'lucide-react';
import { cn } from '@/lib/utils';

interface MoodChipProps {
  mood?: string | null;
  className?: string;
}

const moodConfig: Record<string, { icon: React.ElementType, color: string, bg: string }> = {
  happy: { icon: Smile, color: 'text-green-500', bg: 'bg-green-500/10' },
  sad: { icon: Frown, color: 'text-blue-500', bg: 'bg-blue-500/10' },
  angry: { icon: AlertCircle, color: 'text-red-500', bg: 'bg-red-500/10' },
  surprise: { icon: HelpCircle, color: 'text-yellow-500', bg: 'bg-yellow-500/10' },
  neutral: { icon: Meh, color: 'text-gray-500', bg: 'bg-gray-500/10' },
  fear: { icon: Frown, color: 'text-purple-500', bg: 'bg-purple-500/10' },
  disgust: { icon: AlertCircle, color: 'text-orange-500', bg: 'bg-orange-500/10' },
  confused: { icon: HelpCircle, color: 'text-amber-500', bg: 'bg-amber-500/10' },
};

export function MoodChip({ mood, className }: MoodChipProps) {
  if (!mood) return null;
  
  const normalizedMood = mood.toLowerCase();
  const config = moodConfig[normalizedMood] || moodConfig.neutral;
  const Icon = config.icon;

  return (
    <div className={cn("inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium border border-transparent", config.color, config.bg, className)}>
      <Icon className="w-3.5 h-3.5" />
      <span className="capitalize">{mood}</span>
    </div>
  );
}
