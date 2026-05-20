import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDate(value?: string | number | Date | null) {
  if (!value) return "-";
  const d = new Date(value);
  return new Intl.DateTimeFormat("en", { dateStyle: "medium", timeStyle: "short" }).format(d);
}
