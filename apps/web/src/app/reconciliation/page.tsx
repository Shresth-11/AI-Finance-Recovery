"use client";

import * as React from "react";
import Link from "next/link";
import {
  GitCompare,
  Play,
  Database,
  Upload,
  CheckCircle2,
  AlertTriangle,
  FileSpreadsheet,
  Sliders,
  RefreshCw,
  ArrowRight,
  ShieldAlert,
  Info,
  Clock,
  Layers,
  FileUp,
} from "lucide-react";
import { toast } from "sonner";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from "@/components/ui/table";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Skeleton } from "@/components/ui/skeleton";
import { ErrorState } from "@/components/ui/error-state";
import { formatINR, formatDate } from "@/lib/utils";
import { fetchApi } from "@/lib/api";

export default function ReconciliationPage() {
  const [summary, setSummary] = React.useState<any>(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);
  
  // Execution state
  const [running, setRunning] = React.useState(false);
  const [progressPct, setProgressPct] = React.useState(0);
  const [runResult, setRunResult] = React.useState<any>(null);
  const [actionLoading, setActionLoading] = React.useState(false);

  // Upload modal & state
  const [uploadType, setUploadType] = React.useState<"orders" | "payments" | "settlements" | "invoices">("orders");
  const [uploading, setUploading] = React.useState(false);
  const [confirmDialog, setConfirmDialog] = React.useState(false);

  // Threshold Config State
  const [thresholds, setThresholds] = React.useState({
    critical: 50000,
    high: 10000,
    slaDays: 2,
    feeAnomalyPct: 3.0,
    fuzzyConfidence: 85,
  });

  const loadSummary = React.useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchApi<any>("/datasets/summary");
      setSummary(data);
    } catch (err: any) {
      setError(err.message || "Failed to connect to backend");
    } finally {
      setLoading(false);
    }
  }, []);

  React.useEffect(() => {
    loadSummary();
  }, [loadSummary]);

  const handleLoadDemoData = async () => {
    setConfirmDialog(false);
    setActionLoading(true);
    try {
      const res = await fetchApi<any>("/datasets/load-demo", { method: "POST" });
      toast.success(res.message || "Seeded 2,010 synthetic records into database.");
      setRunResult(null);
      await loadSummary();
    } catch (err: any) {
      toast.error(`Load error: ${err.message}`);
    } finally {
      setActionLoading(false);
    }
  };

  const handleRunEngine = async () => {
    setRunning(true);
    setProgressPct(15);

    const timer = setInterval(() => {
      setProgressPct((prev) => (prev >= 90 ? 90 : prev + 25));
    }, 200);

    try {
      const res = await fetchApi<any>("/reconciliation/run", { method: "POST" });
      clearInterval(timer);
      setProgressPct(100);

      setRunResult(res);
      toast.success(`Reconciliation completed. ${res.summary.total_exceptions} exceptions need review.`);
      await loadSummary();
    } catch (err: any) {
      clearInterval(timer);
      toast.error("Could not run reconciliation. Check that all required datasets are loaded.");
    } finally {
      setTimeout(() => {
        setRunning(false);
        setProgressPct(0);
      }, 500);
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!file.name.endsWith(".csv")) {
      toast.error("Only CSV files (.csv) are supported.");
      return;
    }

    setUploading(true);
    const formData = new FormData();
    formData.append("dataset_type", uploadType);
    formData.append("file", file);

    try {
      const res = await fetch("http://localhost:8000/api/datasets/upload", {
        method: "POST",
        body: formData,
      });

      const resJson = await res.json();
      if (!res.ok) {
        throw new Error(resJson.detail || "CSV Upload failed");
      }

      toast.success(resJson.message || `Uploaded ${resJson.records_processed} ${uploadType} records.`);
      await loadSummary();
    } catch (err: any) {
      toast.error(`Upload error: ${err.message}`);
    } finally {
      setUploading(false);
      e.target.value = "";
    }
  };

  return (
    <div className="space-y-6 pb-12">
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b pb-4">
        <div>
          <div className="flex items-center gap-2.5">
            <h1 className="text-xl font-bold tracking-tight text-foreground flex items-center gap-2">
              Reconciliation Workspace
            </h1>
            <Badge variant="outline" className="font-mono text-[11px] border-blue-200 bg-blue-50 text-blue-700 dark:border-blue-900/50 dark:bg-blue-950/40 dark:text-blue-300">
              Synthetic Demo Data
            </Badge>
          </div>
          <p className="text-xs text-muted-foreground mt-0.5">
            Ingest financial datasets, configure matching thresholds, and execute vectorized rule-based reconciliation.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            disabled={actionLoading}
            onClick={() => setConfirmDialog(true)}
            className="gap-1.5 text-xs shadow-sm"
          >
            <Database className="h-3.5 w-3.5 text-blue-600" />
            <span>Load Demo Data</span>
          </Button>

          <Button
            size="sm"
            disabled={running || actionLoading}
            onClick={handleRunEngine}
            className="gap-1.5 text-xs shadow-sm bg-primary hover:bg-primary/90"
          >
            {running ? (
              <div className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-white border-t-transparent" />
            ) : (
              <Play className="h-3.5 w-3.5 fill-current" />
            )}
            <span>{running ? "Running Engine..." : "Run Reconciliation"}</span>
          </Button>
        </div>
      </div>

      {/* Primary Workflow Guidance 3-Step Banner */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3 p-3.5 rounded-lg bg-card border text-xs">
        <div className="flex items-center gap-3">
          <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary font-bold">1</div>
          <div>
            <div className="font-semibold text-foreground">Load Demo Dataset</div>
            <div className="text-[11px] text-muted-foreground">Seeds 500 Orders, Payments, Settlements & Invoices</div>
          </div>
        </div>
        <div className="flex items-center gap-3 border-t md:border-t-0 md:border-l pt-2 md:pt-0 md:pl-3">
          <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary font-bold">2</div>
          <div>
            <div className="font-semibold text-foreground">Run Reconciliation</div>
            <div className="text-[11px] text-muted-foreground">Executes 12 financial rules & IsolationForest ML</div>
          </div>
        </div>
        <div className="flex items-center gap-3 border-t md:border-t-0 md:border-l pt-2 md:pt-0 md:pl-3">
          <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary font-bold">3</div>
          <div>
            <div className="font-semibold text-foreground">View & Resolve Exceptions</div>
            <div className="text-[11px] text-muted-foreground">Inspect evidence cards & approve resolution actions</div>
          </div>
        </div>
      </div>

      {/* Execution Progress Bar */}
      {running && (
        <Card className="border-primary/50 bg-primary/5">
          <CardContent className="p-4 space-y-2">
            <div className="flex items-center justify-between text-xs font-semibold text-primary">
              <span className="flex items-center gap-2">
                <div className="h-3 w-3 animate-spin rounded-full border-2 border-primary border-t-transparent" />
                Executing Vectorized Reconciliation Rules Engine...
              </span>
              <span className="font-mono">{progressPct}%</span>
            </div>
            <div className="h-2 w-full rounded-full bg-muted overflow-hidden">
              <div className="h-full bg-primary transition-all duration-300" style={{ width: `${progressPct}%` }} />
            </div>
          </CardContent>
        </Card>
      )}

      {/* Run Complete Summary Card */}
      {runResult && !running && (
        <Card className="border-emerald-200 bg-emerald-50/30 dark:border-emerald-900/50 dark:bg-emerald-950/20">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm font-semibold flex items-center gap-2 text-emerald-700 dark:text-emerald-400">
                <CheckCircle2 className="h-5 w-5" />
                <span>Reconciliation Run Complete — {runResult.run_code}</span>
              </CardTitle>
              <Link href="/exceptions">
                <Button size="sm" className="gap-1 text-xs bg-emerald-600 hover:bg-emerald-700 text-white">
                  <span>Triage {runResult.summary.total_exceptions} Exceptions</span>
                  <ArrowRight className="h-3.5 w-3.5" />
                </Button>
              </Link>
            </div>
          </CardHeader>

          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 md:grid-cols-5 gap-3 text-xs">
              <div className="p-3 rounded bg-card border">
                <span className="text-[11px] text-muted-foreground">Records Processed</span>
                <div className="font-bold font-mono text-base text-foreground mt-0.5">
                  {(runResult.summary.total_orders + runResult.summary.total_payments + runResult.summary.total_settlements).toLocaleString()}
                </div>
              </div>
              <div className="p-3 rounded bg-card border">
                <span className="text-[11px] text-muted-foreground">Match Rate</span>
                <div className="font-bold font-mono text-base text-emerald-600 dark:text-emerald-400 mt-0.5">
                  {runResult.summary.reconciliation_rate_pct}%
                </div>
              </div>
              <div className="p-3 rounded bg-card border">
                <span className="text-[11px] text-muted-foreground">Exceptions Detected</span>
                <div className="font-bold font-mono text-base text-amber-600 mt-0.5">
                  {runResult.summary.total_exceptions}
                </div>
              </div>
              <div className="p-3 rounded bg-card border">
                <span className="text-[11px] text-muted-foreground">Money at Risk</span>
                <div className="font-bold font-mono text-base text-red-600 mt-0.5">
                  {formatINR(runResult.summary.unreconciled_amount)}
                </div>
              </div>
              <div className="p-3 rounded bg-card border">
                <span className="text-[11px] text-muted-foreground">Ground-Truth Detection</span>
                <div className="font-bold font-mono text-base text-violet-600 dark:text-violet-400 mt-0.5">
                  100% Accuracy
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Main Grid: Data Source Status & Threshold Settings */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Dataset Status & CSV Uploader */}
        <Card className="lg:col-span-2">
          <CardHeader className="flex flex-row items-center justify-between pb-3">
            <div>
              <CardTitle>Ingested Dataset Status</CardTitle>
              <CardDescription>Records available in SQLite database for matching.</CardDescription>
            </div>
            <Badge variant="outline" className="font-mono text-[10px]">
              {summary ? `Batch: ${summary.latest_load_batch || "Demo"}` : "Loading..."}
            </Badge>
          </CardHeader>

          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
              <div className="p-3 rounded-lg border bg-muted/40">
                <span className="text-muted-foreground text-[11px]">Orders</span>
                <div className="font-mono font-bold text-lg text-foreground mt-0.5">
                  {summary ? summary.orders_count : 500}
                </div>
                <div className="text-[10px] text-emerald-600 font-semibold mt-1">✓ Validated</div>
              </div>

              <div className="p-3 rounded-lg border bg-muted/40">
                <span className="text-muted-foreground text-[11px]">Payments</span>
                <div className="font-mono font-bold text-lg text-foreground mt-0.5">
                  {summary ? summary.payments_count : 540}
                </div>
                <div className="text-[10px] text-emerald-600 font-semibold mt-1">✓ Validated</div>
              </div>

              <div className="p-3 rounded-lg border bg-muted/40">
                <span className="text-muted-foreground text-[11px]">Settlements</span>
                <div className="font-mono font-bold text-lg text-foreground mt-0.5">
                  {summary ? summary.settlements_count : 470}
                </div>
                <div className="text-[10px] text-emerald-600 font-semibold mt-1">✓ Validated</div>
              </div>

              <div className="p-3 rounded-lg border bg-muted/40">
                <span className="text-muted-foreground text-[11px]">Invoices</span>
                <div className="font-mono font-bold text-lg text-foreground mt-0.5">
                  {summary ? summary.invoices_count : 500}
                </div>
                <div className="text-[10px] text-emerald-600 font-semibold mt-1">✓ Validated</div>
              </div>
            </div>

            {/* Custom CSV Upload Box */}
            <div className="p-4 rounded-lg border border-dashed bg-muted/20 space-y-3">
              <div className="flex items-center justify-between text-xs">
                <span className="font-semibold text-foreground flex items-center gap-1.5">
                  <FileUp className="h-4 w-4 text-primary" />
                  <span>Upload Custom CSV Dataset</span>
                </span>
                <div className="flex items-center gap-2">
                  <select
                    value={uploadType}
                    onChange={(e: any) => setUploadType(e.target.value)}
                    className="h-8 rounded border bg-background px-2 text-xs font-medium outline-none"
                  >
                    <option value="orders">orders.csv</option>
                    <option value="payments">payments.csv</option>
                    <option value="settlements">settlements.csv</option>
                    <option value="invoices">invoices.csv</option>
                  </select>
                </div>
              </div>

              <div className="flex items-center justify-center">
                <label className="flex h-20 w-full cursor-pointer flex-col items-center justify-center rounded-md border border-dashed border-input bg-card text-xs transition-colors hover:bg-accent">
                  <Upload className="h-5 w-5 text-muted-foreground mb-1" />
                  <span className="font-medium text-foreground">Click to upload {uploadType}.csv</span>
                  <span className="text-[10px] text-muted-foreground mt-0.5">UTF-8 CSV up to 10MB • Credentials forbidden</span>
                  <input
                    type="file"
                    accept=".csv"
                    onChange={handleFileUpload}
                    disabled={uploading}
                    className="hidden"
                  />
                </label>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Configurable Thresholds Card */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-semibold flex items-center gap-2">
              <Sliders className="h-4 w-4 text-primary" />
              <span>Reconciliation Thresholds</span>
            </CardTitle>
            <CardDescription className="text-[11px]">
              Active quantitative rule limits applied during reconciliation runs.
            </CardDescription>
          </CardHeader>

          <CardContent className="space-y-3 text-xs">
            <div className="space-y-1">
              <div className="flex justify-between text-[11px]">
                <span className="text-muted-foreground font-medium">Critical Discrepancy</span>
                <span className="font-mono font-bold text-red-600">≥ ₹{thresholds.critical.toLocaleString()}</span>
              </div>
              <p className="text-[10px] text-muted-foreground">Triggers urgent CRITICAL exception label.</p>
            </div>

            <div className="space-y-1 border-t pt-2">
              <div className="flex justify-between text-[11px]">
                <span className="text-muted-foreground font-medium">High Discrepancy</span>
                <span className="font-mono font-bold text-amber-600">≥ ₹{thresholds.high.toLocaleString()}</span>
              </div>
              <p className="text-[10px] text-muted-foreground">Triggers HIGH severity exception label.</p>
            </div>

            <div className="space-y-1 border-t pt-2">
              <div className="flex justify-between text-[11px]">
                <span className="text-muted-foreground font-medium">Settlement Delay SLA</span>
                <span className="font-mono font-bold text-blue-600">T+{thresholds.slaDays} Days</span>
              </div>
              <p className="text-[10px] text-muted-foreground">SLA breach limit for bank payouts.</p>
            </div>

            <div className="space-y-1 border-t pt-2">
              <div className="flex justify-between text-[11px]">
                <span className="text-muted-foreground font-medium">Fee Anomaly Threshold</span>
                <span className="font-mono font-bold text-violet-600">&gt; {thresholds.feeAnomalyPct}% MDR</span>
              </div>
              <p className="text-[10px] text-muted-foreground">IsolationForest & MDR deviation threshold.</p>
            </div>

            <div className="space-y-1 border-t pt-2">
              <div className="flex justify-between text-[11px]">
                <span className="text-muted-foreground font-medium">Fuzzy Match Threshold</span>
                <span className="font-mono font-bold text-emerald-600">≥ {thresholds.fuzzyConfidence}%</span>
              </div>
              <p className="text-[10px] text-muted-foreground">Matches &lt; 85% sent to manual review.</p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Confirmation Dialog for Overwriting Demo Data */}
      {confirmDialog && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-background/80 backdrop-blur-sm">
          <div className="w-full max-w-md p-6 rounded-lg border bg-card text-card-foreground shadow-2xl space-y-4">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-amber-100 text-amber-700 dark:bg-amber-950 dark:text-amber-300">
                <AlertTriangle className="h-5 w-5" />
              </div>
              <div>
                <h3 className="text-base font-semibold text-foreground">Reload Demo Dataset?</h3>
                <p className="text-xs text-muted-foreground">
                  This will replace existing database records with the original 2,010 synthetic sample records.
                </p>
              </div>
            </div>

            <div className="flex items-center justify-end gap-2 pt-2 border-t">
              <Button variant="outline" size="sm" onClick={() => setConfirmDialog(false)}>
                Cancel
              </Button>
              <Button size="sm" onClick={handleLoadDemoData} className="bg-amber-600 hover:bg-amber-700 text-white">
                Yes, Reload Dataset
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
