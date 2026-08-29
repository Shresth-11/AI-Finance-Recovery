"use client";

import * as React from "react";
import { useTheme } from "next-themes";
import {
  Search,
  Sun,
  Moon,
  Play,
  Bell,
  Database,
  Sparkles,
} from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { DemoTour } from "./demo-tour";

interface TopbarProps {
  onOpenCommandPalette: () => void;
}

export function Topbar({ onOpenCommandPalette }: TopbarProps) {
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = React.useState(false);

  React.useEffect(() => {
    setMounted(true);
  }, []);

  return (
    <header className="flex h-14 items-center justify-between border-b bg-card px-4 z-20 gap-2">
      {/* Left: Search / Command Palette Trigger */}
      <div className="flex items-center gap-3">
        <button
          onClick={onOpenCommandPalette}
          className="flex h-9 w-48 md:w-72 items-center justify-between rounded-md border border-input bg-muted/40 px-3 text-xs text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
        >
          <div className="flex items-center gap-2">
            <Search className="h-3.5 w-3.5" />
            <span className="truncate">Search exception IDs, UTRs, orders...</span>
          </div>
          <kbd className="pointer-events-none hidden sm:inline-flex h-5 select-none items-center gap-1 rounded border bg-muted px-1.5 font-mono text-[10px] font-medium text-muted-foreground">
            <span className="text-xs">⌘</span>K
          </kbd>
        </button>
      </div>

      {/* Center/Right: 1-Click Judge Demo Preset */}
      <div className="flex items-center gap-2">
        <DemoTour />

        {/* Synthetic Demo Badge */}
        <Badge variant="outline" className="hidden lg:flex items-center gap-1 text-[11px] font-normal border-blue-200 bg-blue-50/50 text-blue-700 dark:border-blue-900/50 dark:bg-blue-950/40 dark:text-blue-300">
          <Database className="h-3 w-3 text-blue-600" />
          <span>Synthetic Demo Data</span>
        </Badge>

        {/* Notifications */}
        <Button variant="ghost" size="icon" className="h-8 w-8 relative text-muted-foreground hover:text-foreground" onClick={() => toast.info("System Alerts", { description: "227 open exception items pending triage." })}>
          <Bell className="h-4 w-4" />
          <span className="absolute top-1 right-1 h-2 w-2 rounded-full bg-blue-600" />
        </Button>

        {/* Theme Switcher Toggle */}
        {mounted && (
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8 text-muted-foreground hover:text-foreground"
            onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
            aria-label="Toggle light/dark theme"
          >
            {theme === "dark" ? <Sun className="h-4 w-4 text-amber-400" /> : <Moon className="h-4 w-4" />}
          </Button>
        )}

        {/* User Menu Avatar */}
        <div className="flex items-center gap-2 border-l pl-2 ml-1">
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary/10 text-primary font-semibold text-xs border border-primary/20" title="Finance Controller Role">
            FC
          </div>
        </div>
      </div>
    </header>
  );
}
