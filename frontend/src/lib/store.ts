"use client";

import { create } from "zustand";

type ThemeState = {
  darkMode: boolean;
  toggle: () => void;
  setDarkMode: (dark: boolean) => void;
};

export const useThemeStore = create<ThemeState>((set) => ({
  darkMode: true,
  toggle: () => set((s) => ({ darkMode: !s.darkMode })),
  setDarkMode: (dark) => set({ darkMode: dark }),
}));
