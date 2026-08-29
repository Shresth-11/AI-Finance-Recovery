"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { Sparkles, Play, AlertTriangle, ArrowRight, CheckCircle2, ShieldAlert } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { fetchApi } from "@/lib/api";

interface DemoTourProps {
  onRunReconciliation?: () => void;
}

export function DemoTour({ onRunReconciliation }: DemoTourProps) {
  const router = useRouter();
  const [running, setRunning] = React.useState(false);

  const handleQuickDemoFlow = async () => {
    setRunning(true);
    toast.info("⚡ Executing 30-Second Judge Demo Preset...", {
      description: "1. Seeding 2,010 records → 2. Running 12-rule engine → 3. Navigating to Critical Exceptions.",
    });

    try {
      // 1. Seed demo dataset
      await fetchApi("/datasets/load-demo", { method: "POST" });
      
      // 2. Run reconciliation engine
      const res = await fetchApi<any>("/reconciliation/run", { method: "POST" });
      
      toast.success(`Reconciliation Completed! Detected ${res.summary.total_exceptions} exceptions.`, {
        description: "Navigating to Critical Exceptions Triage Queue...",
      });

      // 3. Navigate to exceptions queue
      router.push("/exceptions?severity=CRITICAL&status=OPEN");
    } catch (err: any) {
      toast.error(`Demo preset failed: ${err.message}`);
    } finally {
      setRunning(false);
    }
  };

  return (
    <div className="flex items-center gap-2 bg-gradient-to-r from-violet-600/10 via-primary/10 to-emerald-600/10 p-1.5 rounded-lg border border-violet-300/40 dark:border-violet-800/40 shadow-xs">
      <div className="flex items-center gap-1.5 px-2 text-xs font-bold text-violet-700 dark:text-violet-300">
        <Sparkles className="h-3.5 w-3.5 fill-current animate-pulse" />
        <span className="hidden sm:inline uppercase text-[10px] tracking-wider font-extrabold">Judge Demo Shortcut</span>
      </div>

      <Button
        size="sm"
        disabled={running}
        onClick={handleQuickDemoFlow}
        className="h-7 text-[11px] gap-1 px-2.5 bg-violet-600 hover:bg-violet-700 text-white font-semibold shadow-xs"
      >
        {running ? (
          <div className="h-3 w-3 animate-spin rounded-full border-2 border-white border-t-transparent" />
        ) : (
          <Play className="h-3 w-3 fill-current" />
        )}
        <span>{running ? "Executing Preset..." : "Run 1-Click Judge Demo"}</span>
      </Button>
    </div>
  );
}
