"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { Play, Database } from "lucide-react";
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
    toast.info("Loading demo data and running reconciliation...", {
      description: "Processing 2,010 records across orders, payments, settlements, and invoices.",
    });

    try {
      // 1. Seed demo dataset
      await fetchApi("/datasets/load-demo", { method: "POST" });
      
      // 2. Run reconciliation engine
      const res = await fetchApi<any>("/reconciliation/run", { method: "POST" });
      
      toast.success(`Reconciliation complete. Detected ${res.summary.total_exceptions} exceptions requiring review.`, {
        description: "Opening critical exceptions queue.",
      });

      // 3. Navigate to open critical exceptions queue
      router.push("/exceptions?severity=CRITICAL&status=OPEN");
    } catch (err: any) {
      toast.error(`Unable to run demo dataset: ${err.message}`);
    } finally {
      setRunning(false);
    }
  };

  return (
    <div className="flex items-center gap-2 bg-muted/50 p-1 rounded border border-border">
      <div className="flex items-center gap-1.5 px-2 text-xs font-medium text-muted-foreground">
        <Database className="h-3.5 w-3.5 text-primary" />
        <span className="hidden sm:inline text-[11px]">Demo Data</span>
      </div>

      <Button
        size="sm"
        disabled={running}
        onClick={handleQuickDemoFlow}
        className="h-7 text-xs gap-1.5 px-3 font-medium"
      >
        {running ? (
          <div className="h-3 w-3 animate-spin rounded-full border-2 border-primary-foreground border-t-transparent" />
        ) : (
          <Play className="h-3 w-3 fill-current" />
        )}
        <span>{running ? "Processing..." : "Run Demo Preset"}</span>
      </Button>
    </div>
  );
}
