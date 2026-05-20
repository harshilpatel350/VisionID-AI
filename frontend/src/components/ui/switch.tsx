"use client";

import * as SwitchPrimitive from "@radix-ui/react-switch";
import { cn } from "@/lib/utils";

export function Switch({ className, ...props }: SwitchPrimitive.SwitchProps) {
  return (
    <SwitchPrimitive.Root className={cn("h-6 w-11 rounded-full border border-white/10 bg-white/10 p-0.5 data-[state=checked]:bg-indigo-500", className)} {...props}>
      <SwitchPrimitive.Thumb className="block h-5 w-5 rounded-full bg-white transition-transform data-[state=checked]:translate-x-5" />
    </SwitchPrimitive.Root>
  );
}
