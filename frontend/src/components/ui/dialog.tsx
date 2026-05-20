"use client";

import * as DialogPrimitive from "@radix-ui/react-dialog";
import { X } from "lucide-react";
import { cn } from "@/lib/utils";

export const Dialog = DialogPrimitive.Root;
export const DialogTrigger = DialogPrimitive.Trigger;
export const DialogPortal = DialogPrimitive.Portal;
export const DialogClose = DialogPrimitive.Close;

export function DialogContent({ className, children, ...props }: DialogPrimitive.DialogContentProps) {
  return (
    <DialogPortal>
      <DialogPrimitive.Overlay className="fixed inset-0 bg-black/60 backdrop-blur-sm" />
      <DialogPrimitive.Content className={cn("fixed left-1/2 top-1/2 w-[min(92vw,860px)] -translate-x-1/2 -translate-y-1/2 rounded-3xl border border-white/10 bg-slate-950 p-5 shadow-2xl", className)} {...props}>
        <DialogPrimitive.Close className="absolute right-4 top-4 rounded-lg p-2 text-slate-400 hover:bg-white/10 hover:text-white">
          <X className="h-4 w-4" />
        </DialogPrimitive.Close>
        {children}
      </DialogPrimitive.Content>
    </DialogPortal>
  );
}

export const DialogTitle = DialogPrimitive.Title;
export const DialogDescription = DialogPrimitive.Description;
