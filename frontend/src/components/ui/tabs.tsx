"use client";

import * as TabsPrimitive from "@radix-ui/react-tabs";
import { cn } from "@/lib/utils";

export const Tabs = TabsPrimitive.Root;
export const TabsList = ({ className, ...props }: TabsPrimitive.TabsListProps) => (
  <TabsPrimitive.List className={cn("inline-flex rounded-2xl border border-white/10 bg-white/5 p-1", className)} {...props} />
);
export const TabsTrigger = ({ className, ...props }: TabsPrimitive.TabsTriggerProps) => (
  <TabsPrimitive.Trigger className={cn("rounded-xl px-3 py-1.5 text-sm text-slate-300 transition data-[state=active]:bg-white/10 data-[state=active]:text-white", className)} {...props} />
);
export const TabsContent = TabsPrimitive.Content;
