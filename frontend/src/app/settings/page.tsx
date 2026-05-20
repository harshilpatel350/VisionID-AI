"use client";

import { AppShell } from "@/components/app-shell";
import { Card, CardContent, CardTitle } from "@/components/ui/card";
import { Switch } from "@/components/ui/switch";
import { useThemeStore } from "@/lib/store";

export default function SettingsPage() {
  const { darkMode, toggle } = useThemeStore();
  return (
    <AppShell>
      <Card>
        <CardTitle>Settings</CardTitle>
        <CardContent className="mt-4 flex items-center justify-between">
          <div>
            <div className="font-medium">Dark mode</div>
            <div className="text-sm text-slate-400">Current theme: {darkMode ? "dark" : "light"}</div>
          </div>
          <Switch checked={darkMode} onCheckedChange={toggle} />
        </CardContent>
      </Card>
    </AppShell>
  );
}
