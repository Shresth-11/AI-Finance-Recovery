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
          className="flex h-9 w-48 md:w-72 items-center justify-between rounded-md border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 px-3 text-xs text-slate-700 dark:text-slate-300 font-medium transition-all hover:border-blue-600 shadow-xs"
        >
          <div className="flex items-center gap-2">
            <Search className="h-3.5 w-3.5 text-slate-500 dark:text-slate-400" />
            <span className="truncate">Search exception IDs, UTRs, orders...</span>
          </div>
          <kbd className="pointer-events-none hidden sm:inline-flex h-5 select-none items-center gap-1 rounded border border-slate-300 dark:border-slate-700 bg-slate-100 dark:bg-slate-800 px-1.5 font-mono text-[10px] font-bold text-slate-800 dark:text-slate-200">
            <span className="text-xs">⌘</span>K
          </kbd>
        </button>
      </div>

      {/* Center/Right: 1-Click Judge Demo Preset */}
      <div className="flex items-center gap-2">
        <DemoTour />

        {/* Synthetic Demo Badge */}
        <Badge variant="outline" className="hidden lg:flex items-center gap-1 text-xs font-bold border-blue-300 bg-blue-100/90 text-blue-900 dark:border-blue-800 dark:bg-blue-950 dark:text-blue-200">
          <Database className="h-3.5 w-3.5 text-blue-700 dark:text-blue-400" />
          <span>Synthetic Demo Data</span>
        </Badge>

        {/* Notifications */}
        <Button variant="ghost" size="icon" className="h-8 w-8 relative text-slate-700 dark:text-slate-300 hover:text-slate-950 dark:hover:text-white" onClick={() => toast.info("System Alerts", { description: "227 open exception items pending triage." })}>
          <Bell className="h-4 w-4" />
          <span className="absolute top-1 right-1 h-2 w-2 rounded-full bg-blue-600" />
        </Button>

        {/* Theme Switcher Toggle */}
        {mounted && (
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8 text-slate-700 dark:text-slate-300 hover:text-slate-950 dark:hover:text-white"
            onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
            aria-label="Toggle light/dark theme"
          >
            {theme === "dark" ? <Sun className="h-4 w-4 text-amber-400" /> : <Moon className="h-4 w-4" />}
          </Button>
        )}

        {/* User Menu Avatar */}
        <div className="flex items-center gap-2 border-l border-slate-300 dark:border-slate-700 pl-2 ml-1">
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-blue-600 text-white font-bold text-xs shadow-xs" title="Finance Controller Role">
            FC
          </div>
        </div>
      </div>
    </header>
  );
}
