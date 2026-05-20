import * as React from "react";
import { cn } from "@/lib/utils";

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "default" | "secondary" | "outline" | "ghost" | "destructive";
  size?: "sm" | "default" | "lg";
}

const styles: Record<NonNullable<ButtonProps["variant"]>, string> = {
  default: "bg-indigo-500 text-white hover:bg-indigo-400",
  secondary: "bg-white/10 text-slate-100 hover:bg-white/15",
  outline: "border border-white/15 bg-transparent text-slate-100 hover:bg-white/5",
  ghost: "bg-transparent text-slate-100 hover:bg-white/5",
  destructive: "bg-rose-500 text-white hover:bg-rose-400",
};

const sizes: Record<NonNullable<ButtonProps["size"]>, string> = {
  sm: "h-8 px-3 text-xs",
  default: "h-10 px-4 text-sm",
  lg: "h-12 px-5 text-base",
};

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "default", size = "default", ...props }, ref) => (
    <button
      ref={ref}
      className={cn(
        "inline-flex items-center justify-center rounded-xl font-medium transition active:scale-[0.99] disabled:opacity-50",
        styles[variant],
        sizes[size],
        className
      )}
      {...props}
    />
  )
);
Button.displayName = "Button";
