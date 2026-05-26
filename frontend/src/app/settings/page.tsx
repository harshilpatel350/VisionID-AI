"use client";

import { AppShell } from "@/components/app-shell";
import { Card, CardContent, CardTitle } from "@/components/ui/card";
import { Switch } from "@/components/ui/switch";
import { useThemeStore } from "@/lib/store";

export default function SettingsPage() {
  const { darkMode, toggle } = useThemeStore();
  return (
    <AppShell>
      <Card className="glass-violet border-primary/20">
        <CardTitle className="text-white">Settings</CardTitle>
        <CardContent className="mt-4 flex items-center justify-between">
          <div>
            <div className="font-medium text-white">Dark mode</div>
            <div className="text-sm text-muted">Current theme: {darkMode ? "dark" : "light"}</div>
          </div>
          <Switch checked={darkMode} onCheckedChange={toggle} />
        </CardContent>
      </Card>
    </AppShell>
  );
}
