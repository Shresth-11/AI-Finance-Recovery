"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import {
  Search,
  LayoutDashboard,
  GitCompare,
  AlertTriangle,
  FileSpreadsheet,
  Sparkles,
  BookOpen,
  Settings,
  Play,
  Download,
  RotateCcw,
} from "lucide-react";
import { toast } from "sonner";

interface CommandPaletteProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function CommandPalette({ open, onOpenChange }: CommandPaletteProps) {
  const router = useRouter();
  const [query, setQuery] = React.useState("");

  React.useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        onOpenChange(!open);
      }
      if (e.key === "Escape" && open) {
        onOpenChange(false);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [open, onOpenChange]);

  if (!open) return null;

  const navigate = (href: string) => {
    onOpenChange(false);
    setQuery("");
    router.push(href);
  };

  const handleAction = (actionName: string) => {
    onOpenChange(false);
    setQuery("");
    toast.success(`Triggered: ${actionName}`);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-20 bg-background/80 backdrop-blur-sm animate-in fade-in-0">
      <div
        className="fixed inset-0"
        onClick={() => onOpenChange(false)}
      />
      <div className="relative w-full max-w-lg overflow-hidden rounded-xl border bg-popover text-popover-foreground shadow-2xl z-50">
        {/* Search Input Header */}
        <div className="flex items-center border-b px-3">
          <Search className="h-4 w-4 shrink-0 text-muted-foreground mr-2" />
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Type a command or search exceptions..."
            className="flex h-11 w-full rounded-md bg-transparent text-sm outline-none placeholder:text-muted-foreground"
            autoFocus
          />
          <span className="text-[10px] text-muted-foreground font-mono bg-muted px-1.5 py-0.5 rounded">ESC to close</span>
        </div>

        {/* Command Items */}
        <div className="max-h-80 overflow-y-auto p-2">
          {/* Navigation Section */}
          <div className="px-2 py-1.5 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
            Navigation
          </div>

          <div
            onClick={() => navigate("/")}
            className="flex items-center gap-2.5 rounded-md px-2 py-2 text-xs hover:bg-accent hover:text-accent-foreground cursor-pointer"
          >
            <LayoutDashboard className="h-4 w-4 text-muted-foreground" />
            <span>Overview Dashboard</span>
          </div>

          <div
            onClick={() => navigate("/reconciliation")}
            className="flex items-center gap-2.5 rounded-md px-2 py-2 text-xs hover:bg-accent hover:text-accent-foreground cursor-pointer"
          >
            <GitCompare className="h-4 w-4 text-muted-foreground" />
            <span>Reconciliation Console</span>
          </div>

          <div
            onClick={() => navigate("/exceptions")}
            className="flex items-center gap-2.5 rounded-md px-2 py-2 text-xs hover:bg-accent hover:text-accent-foreground cursor-pointer"
          >
            <AlertTriangle className="h-4 w-4 text-muted-foreground" />
            <span>Exceptions Triage</span>
          </div>

          <div
            onClick={() => navigate("/reports")}
            className="flex items-center gap-2.5 rounded-md px-2 py-2 text-xs hover:bg-accent hover:text-accent-foreground cursor-pointer"
          >
            <FileSpreadsheet className="h-4 w-4 text-muted-foreground" />
            <span>Financial Reports & Exports</span>
          </div>

          <div
            onClick={() => navigate("/copilot")}
            className="flex items-center gap-2.5 rounded-md px-2 py-2 text-xs hover:bg-accent hover:text-accent-foreground cursor-pointer"
          >
            <Sparkles className="h-4 w-4 text-violet-500" />
            <span>AI Copilot & Recommendations</span>
          </div>

          <div
            onClick={() => navigate("/methodology")}
            className="flex items-center gap-2.5 rounded-md px-2 py-2 text-xs hover:bg-accent hover:text-accent-foreground cursor-pointer"
          >
            <BookOpen className="h-4 w-4 text-muted-foreground" />
            <span>Reconciliation Methodology</span>
          </div>

          <div
            onClick={() => navigate("/settings")}
            className="flex items-center gap-2.5 rounded-md px-2 py-2 text-xs hover:bg-accent hover:text-accent-foreground cursor-pointer"
          >
            <Settings className="h-4 w-4 text-muted-foreground" />
            <span>Settings & Rules Engine Config</span>
          </div>

          {/* Quick Actions Section */}
          <div className="mt-2 border-t pt-2 px-2 py-1.5 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
            Quick Actions
          </div>

          <div
            onClick={() => handleAction("Run Reconciliation Engine")}
            className="flex items-center gap-2.5 rounded-md px-2 py-2 text-xs hover:bg-accent hover:text-accent-foreground cursor-pointer"
          >
            <Play className="h-4 w-4 text-blue-600" />
            <span>Execute Reconciliation Engine</span>
          </div>

          <div
            onClick={() => handleAction("Export Exception Report CSV")}
            className="flex items-center gap-2.5 rounded-md px-2 py-2 text-xs hover:bg-accent hover:text-accent-foreground cursor-pointer"
          >
            <Download className="h-4 w-4 text-emerald-600" />
            <span>Download Exception CSV Report</span>
          </div>

          <div
            onClick={() => handleAction("Reset Demo Database")}
            className="flex items-center gap-2.5 rounded-md px-2 py-2 text-xs hover:bg-accent hover:text-accent-foreground cursor-pointer"
          >
            <RotateCcw className="h-4 w-4 text-amber-600" />
            <span>Reset Demo Database State</span>
          </div>
        </div>
      </div>
    </div>
  );
}
