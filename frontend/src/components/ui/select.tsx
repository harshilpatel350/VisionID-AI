"use client";

import * as SelectPrimitive from "@radix-ui/react-select";
import { ChevronDown, Check } from "lucide-react";
import { cn } from "@/lib/utils";

export const Select = SelectPrimitive.Root;
export const SelectValue = SelectPrimitive.Value;
export const SelectTrigger = ({ className, children, ...props }: SelectPrimitive.SelectTriggerProps) => (
  <SelectPrimitive.Trigger className={cn("flex h-11 w-full items-center justify-between rounded-xl border border-white/10 bg-white/5 px-4 text-sm text-white", className)} {...props}>
    {children}
    <ChevronDown className="h-4 w-4 text-slate-400" />
  </SelectPrimitive.Trigger>
);
export const SelectContent = ({ className, children, ...props }: SelectPrimitive.SelectContentProps) => (
  <SelectPrimitive.Portal>
    <SelectPrimitive.Content className={cn("z-50 overflow-hidden rounded-2xl border border-white/10 bg-slate-950 p-1 shadow-2xl", className)} {...props}>
      <SelectPrimitive.Viewport>{children}</SelectPrimitive.Viewport>
    </SelectPrimitive.Content>
  </SelectPrimitive.Portal>
);
export const SelectItem = ({ className, children, ...props }: SelectPrimitive.SelectItemProps) => (
  <SelectPrimitive.Item className={cn("relative flex cursor-pointer select-none items-center rounded-xl py-2 pl-8 pr-3 text-sm text-slate-200 outline-none hover:bg-white/10 focus:bg-white/10", className)} {...props}>
    <SelectPrimitive.ItemIndicator className="absolute left-2 inline-flex items-center">
      <Check className="h-4 w-4" />
    </SelectPrimitive.ItemIndicator>
    <SelectPrimitive.ItemText>{children}</SelectPrimitive.ItemText>
  </SelectPrimitive.Item>
);
