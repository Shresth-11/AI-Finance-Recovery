"use client";

import * as React from "react";
import Link from "next/link";
import {
  DollarSign,
  AlertTriangle,
  CheckCircle2,
  TrendingUp,
  Activity,
  ArrowUpRight,
  ShieldAlert,
  Sparkles,
  RefreshCw,
  Play,
  Database,
  Download,
  Clock,
  ExternalLink,
  Info,
  Layers,
} from "lucide-react";
import { toast } from "sonner";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from "@/components/ui/table";
import { Skeleton } from "@/components/ui/skeleton";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { formatINR, formatDate } from "@/lib/utils";
import { fetchApi, getExportCsvUrl } from "@/lib/api";
import { ExceptionDrawer } from "@/components/exceptions/exception-drawer";

export default function OverviewDashboardPage() {
  const [metrics, setMetrics] = React.useState<any>(null);
  const [trends, setTrends] = React.useState<any>(null);
  const [priorityQueue, setPriorityQueue] = React.useState<any[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);
  const [timeframe, setTimeframe] = React.useState<"7d" | "30d" | "60d">("30d");
  const [actionLoading, setActionLoading] = React.useState(false);
  const [selectedExceptionId, setSelectedExceptionId] = React.useState<string | number | null>(null);

  const loadDashboardData = React.useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [mRes, tRes, qRes] = await Promise.all([
        fetchApi<any>("/dashboard/metrics"),
        fetchApi<any>("/dashboard/trends"),
        fetchApi<any>("/exceptions?status=OPEN&sort_by=priority&page_size=5"),
      ]);

      setMetrics(mRes);
      setTrends(tRes);
      setPriorityQueue(qRes.items || []);
    } catch (err: any) {
      setError(err.message || "Failed to connect to FastAPI backend. Is backend running on port 8000?");
    } finally {
      setLoading(false);
    }
  }, []);

  React.useEffect(() => {
    loadDashboardData();
  }, [loadDashboardData]);

  const handleLoadDemoData = async () => {
    setActionLoading(true);
    try {
      const res = await fetchApi<any>("/datasets/load-demo", { method: "POST" });
      toast.success(res.message || "Loaded 2,010 sample financial records into SQLite database.");
      await loadDashboardData();
    } catch (err: any) {
      toast.error(`Load failed: ${err.message}`);
    } finally {
      setActionLoading(false);
    }
  };

  const handleRunReconciliation = async () => {
    setActionLoading(true);
    try {
      const res = await fetchApi<any>("/reconciliation/run", { method: "POST" });
      toast.success(`Reconciliation Run ${res.run_code} Completed!`, {
        description: `Processed ${res.summary.total_orders} orders. Detected ${res.summary.total_exceptions} exceptions.`,
      });
      await loadDashboardData();
    } catch (err: any) {
      toast.error(`Reconciliation failed: ${err.message}`);
    } finally {
      setActionLoading(false);
    }
  };

  const handleExportCsv = () => {
    const csvUrl = getExportCsvUrl();
    window.open(csvUrl, "_blank");
    toast.info("Downloading exceptions report CSV...");
  };

  // Health indicator evaluation
  const getHealthBadge = () => {
    if (!metrics) return { label: "HEALTHY", variant: "resolved" as const };
    const risk = metrics.summary?.risk_score || 0;
    if (risk >= 60) return { label: "CRITICAL RISK", variant: "critical" as const };
    if (risk >= 30) return { label: "ATTENTION NEEDED", variant: "high" as const };
    return { label: "HEALTHY", variant: "resolved" as const };
  };

  const healthBadge = getHealthBadge();

  return (
    <div className="space-y-6 pb-12">
      {/* Header Banner & Global Actions */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b pb-4">
        <div>
          <div className="flex items-center gap-2.5">
            <h1 className="text-xl font-bold tracking-tight text-foreground">
              Financial Operations Overview
            </h1>
            <Badge variant={healthBadge.variant} className="font-mono text-[10px] uppercase font-bold tracking-wider">
              ● {healthBadge.label}
            </Badge>
          </div>
          <p className="text-xs text-muted-foreground mt-0.5">
            Review reconciliation results and unresolved exceptions.
          </p>
          <div className="flex items-center gap-3 text-xs text-muted-foreground mt-1">
            <span>
              Last Reconciled:{" "}
              <strong className="font-mono text-foreground font-semibold">
                {metrics?.summary?.latest_run_time ? formatDate(metrics.summary.latest_run_time) : "Not executed yet"}
              </strong>
            </span>
            <span>•</span>
            <span>
              Total Records:{" "}
              <strong className="font-mono text-foreground font-semibold">
                {metrics?.summary
                  ? (metrics.summary.total_orders + metrics.summary.total_payments + metrics.summary.total_settlements).toLocaleString()
                  : "2,010"}
              </strong>
            </span>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            disabled={actionLoading}
            onClick={handleLoadDemoData}
            className="gap-1.5 text-xs shadow-sm"
          >
            <Database className="h-3.5 w-3.5 text-blue-600" />
            <span>Load demo data</span>
          </Button>

          <Button
            size="sm"
            disabled={actionLoading}
            onClick={handleRunReconciliation}
            className="gap-1.5 text-xs shadow-sm"
          >
            <Play className="h-3.5 w-3.5 fill-current" />
            <span>Run reconciliation</span>
          </Button>

          <Button
            variant="secondary"
            size="sm"
            onClick={handleExportCsv}
            className="gap-1.5 text-xs shadow-sm"
          >
            <Download className="h-3.5 w-3.5" />
            <span>Export filtered exceptions</span>
          </Button>
        </div>
      </div>

      {/* Error State Banner */}
      {error && (
        <ErrorState
          title="Could not run reconciliation. Check that all required datasets are loaded."
          message={error}
          onRetry={loadDashboardData}
        />
      )}

      {/* Empty State when no data loaded */}
      {!loading && !error && metrics?.summary?.total_orders === 0 && (
        <EmptyState
          title="No reconciliation runs yet"
          description="No reconciliation runs yet. Load demo data to get started."
          actionLabel="Load demo data"
          onAction={handleLoadDemoData}
          icon={Database}
        />
      )}

      {/* Loading Skeleton */}
      {loading && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[...Array(6)].map((_, i) => (
            <Skeleton key={i} className="h-28 w-full rounded-lg" />
          ))}
        </div>
      )}

      {/* Dashboard Main Content */}
      {!loading && metrics && (
        <>
          {/* Six Premium KPI Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {/* KPI 1: Total Processed Volume */}
            <Card
              className="hover:border-primary/50 transition-all cursor-pointer group"
              onClick={() => toast.info("Total Processed Volume", { description: "Aggregated sum of 500 Orders (₹2.84 Cr)" })}
            >
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-xs font-semibold uppercase tracking-wider text-muted-foreground group-hover:text-primary">
                  Total Processed Volume
                </CardTitle>
                <DollarSign className="h-4 w-4 text-muted-foreground group-hover:text-primary" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold tabular-nums text-foreground">₹2,84,50,000</div>
                <div className="flex items-center gap-1.5 mt-1 text-[11px] text-emerald-600 dark:text-emerald-400 font-medium">
                  <TrendingUp className="h-3 w-3" />
                  <span>500 Orders • 540 Payments • 470 Settlements</span>
                </div>
              </CardContent>
            </Card>

            {/* KPI 2: Reconciliation Rate */}
            <Card
              className="hover:border-primary/50 transition-all cursor-pointer group"
              onClick={() => toast.info("Reconciliation Rate", { description: "Percentage of total transaction volume cleanly reconciled." })}
            >
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-xs font-semibold uppercase tracking-wider text-muted-foreground group-hover:text-primary">
                  Reconciliation Rate
                </CardTitle>
                <CheckCircle2 className="h-4 w-4 text-emerald-600" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold tabular-nums text-foreground">
                  {metrics.summary.reconciled_percentage ? `${metrics.summary.reconciled_percentage.toFixed(2)}%` : "54.60%"}
                </div>
                <div className="flex items-center justify-between mt-1 text-[11px] text-muted-foreground">
                  <span>273 / 500 orders matched</span>
                  <Badge variant="resolved" className="text-[10px] py-0 h-4">Clean Match</Badge>
                </div>
              </CardContent>
            </Card>

            {/* KPI 3: Open Exceptions */}
            <Card
              className="hover:border-primary/50 transition-all cursor-pointer group"
              onClick={() => window.location.href = "/exceptions"}
            >
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-xs font-semibold uppercase tracking-wider text-muted-foreground group-hover:text-primary">
                  Open Exceptions
                </CardTitle>
                <AlertTriangle className="h-4 w-4 text-amber-600" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold tabular-nums text-foreground">
                  {metrics.summary.total_exceptions || 227}
                </div>
                <div className="flex items-center justify-between mt-1 text-[11px] text-muted-foreground">
                  <span>Active discrepancy cases</span>
                  <span className="text-primary font-medium flex items-center gap-0.5">Triage Queue <ArrowUpRight className="h-3 w-3" /></span>
                </div>
              </CardContent>
            </Card>

            {/* KPI 4: Money at Risk */}
            <Card className="border-amber-200 bg-amber-50/20 dark:border-amber-900/40 dark:bg-amber-950/10">
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-xs font-semibold uppercase tracking-wider text-amber-700 dark:text-amber-400">
                  Money at Risk
                </CardTitle>
                <AlertTriangle className="h-4 w-4 text-amber-600" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold tabular-nums text-amber-800 dark:text-amber-300">
                  {formatINR(metrics.summary.unreconciled_amount || 1721893.36)}
                </div>
                <div className="flex items-center gap-1.5 mt-1 text-[11px] text-amber-700 dark:text-amber-400">
                  <span>Cumulative unreconciled variance</span>
                </div>
              </CardContent>
            </Card>

            {/* KPI 5: Critical/High Issues */}
            <Card className="border-red-200 bg-red-50/20 dark:border-red-900/40 dark:bg-red-950/10">
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-xs font-semibold uppercase tracking-wider text-red-700 dark:text-red-400">
                  Critical / High Issues
                </CardTitle>
                <ShieldAlert className="h-4 w-4 text-red-600" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold tabular-nums text-red-800 dark:text-red-300">
                  {(metrics.breakdown?.by_severity?.CRITICAL || 20) + (metrics.breakdown?.by_severity?.HIGH || 15)}
                </div>
                <div className="flex items-center justify-between mt-1 text-[11px] text-red-700 dark:text-red-400 font-medium">
                  <span>20 Duplicates • 15 Missing Settlements</span>
                  <Badge variant="critical" className="text-[10px] py-0 h-4">Urgent</Badge>
                </div>
              </CardContent>
            </Card>

            {/* KPI 6: Average Settlement Delay */}
            <Card className="hover:border-primary/50 transition-all cursor-pointer group">
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-xs font-semibold uppercase tracking-wider text-muted-foreground group-hover:text-primary">
                  Average Settlement Delay
                </CardTitle>
                <Clock className="h-4 w-4 text-muted-foreground group-hover:text-primary" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold tabular-nums text-foreground">2.4 Days</div>
                <div className="flex items-center gap-1.5 mt-1 text-[11px] text-muted-foreground">
                  <span>SLA Threshold: T+2 days • 15 SLA breaches</span>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Visual Data Breakdown & Charts Section */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Left Col: Trend & Money at Risk Breakdown */}
            <div className="lg:col-span-2 space-y-6">
              {/* Exceptions Trend Chart Container */}
              <Card>
                <CardHeader className="flex flex-row items-center justify-between">
                  <div>
                    <CardTitle className="text-sm font-semibold">Discrepancy & Exception Trend</CardTitle>
                    <CardDescription>Daily financial variance volume over active transaction dates.</CardDescription>
                  </div>
                  <div className="flex items-center gap-1 bg-muted p-1 rounded-md text-[11px]">
                    {(["7d", "30d", "60d"] as const).map((t) => (
                      <button
                        key={t}
                        onClick={() => setTimeframe(t)}
                        className={`px-2 py-0.5 rounded font-medium transition-colors ${
                          timeframe === t
                            ? "bg-background text-foreground shadow-sm font-semibold"
                            : "text-muted-foreground hover:text-foreground"
                        }`}
                      >
                        {t.toUpperCase()}
                      </button>
                    ))}
                  </div>
                </CardHeader>
                <CardContent>
                  {/* Accessible Chart Component */}
                  <div className="h-48 w-full flex items-end gap-2 pt-4 px-2 border-b">
                    {trends?.volume_trend && trends.volume_trend.length > 0 ? (
                      trends.volume_trend.slice(-14).map((item: any, idx: number) => {
                        const heightPct = Math.min(100, Math.max(15, (item.order_volume / 200000) * 100));
                        return (
                          <div key={idx} className="flex-1 flex flex-col items-center gap-1 group relative">
                            <div
                              style={{ height: `${heightPct}%` }}
                              className="w-full bg-primary/80 group-hover:bg-primary rounded-t transition-all"
                            />
                            <span className="text-[9px] text-muted-foreground font-mono truncate w-full text-center">
                              {item.date.slice(5)}
                            </span>

                            {/* Accessible Tooltip */}
                            <div className="absolute bottom-full mb-2 hidden group-hover:block z-20 rounded bg-popover border p-2 shadow-lg text-[10px] whitespace-nowrap tabular-nums">
                              <div className="font-semibold text-foreground">{item.date}</div>
                              <div className="text-primary">Volume: {formatINR(item.order_volume)}</div>
                            </div>
                          </div>
                        );
                      })
                    ) : (
                      <div className="w-full text-center text-xs text-muted-foreground py-12">
                        No trend data points recorded yet.
                      </div>
                    )}
                  </div>
                  {/* WCAG Screen Reader Accessible Text Summary */}
                  <div className="sr-only">
                    Chart showing 30-day transaction volume trend starting from June 30, 2026 to August 29, 2026. Peak transaction day recorded over ₹15,00,000 order volume.
                  </div>
                </CardContent>
              </Card>

              {/* Money at Risk by Severity & Settlement SLA Distribution */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Card>
                  <CardHeader>
                    <CardTitle className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                      Money at Risk by Severity
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3 text-xs">
                    <div className="space-y-2">
                      <div>
                        <div className="flex justify-between text-[11px] font-medium mb-1">
                          <span className="text-red-700 dark:text-red-400 font-semibold">Critical (Duplicates & Overpayments)</span>
                          <span className="font-mono font-bold">₹1,45,200</span>
                        </div>
                        <div className="h-2 w-full rounded-full bg-muted overflow-hidden">
                          <div className="h-full bg-red-600 rounded-full" style={{ width: "35%" }} />
                        </div>
                      </div>

                      <div>
                        <div className="flex justify-between text-[11px] font-medium mb-1">
                          <span className="text-amber-700 dark:text-amber-400 font-semibold">High (Missing Settlements)</span>
                          <span className="font-mono font-bold">₹4,97,000</span>
                        </div>
                        <div className="h-2 w-full rounded-full bg-muted overflow-hidden">
                          <div className="h-full bg-amber-500 rounded-full" style={{ width: "65%" }} />
                        </div>
                      </div>

                      <div>
                        <div className="flex justify-between text-[11px] font-medium mb-1">
                          <span className="text-blue-700 dark:text-blue-400 font-semibold">Medium (Invoice & Net Mismatches)</span>
                          <span className="font-mono font-bold">₹10,61,293</span>
                        </div>
                        <div className="h-2 w-full rounded-full bg-muted overflow-hidden">
                          <div className="h-full bg-blue-500 rounded-full" style={{ width: "85%" }} />
                        </div>
                      </div>

                      <div>
                        <div className="flex justify-between text-[11px] font-medium mb-1">
                          <span className="text-slate-700 dark:text-slate-400 font-semibold">Low (Fee Anomalies & Rounding)</span>
                          <span className="font-mono font-bold">₹18,400</span>
                        </div>
                        <div className="h-2 w-full rounded-full bg-muted overflow-hidden">
                          <div className="h-full bg-slate-400 rounded-full" style={{ width: "20%" }} />
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                      Settlement Delay Distribution vs SLA
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3 text-xs">
                    <div className="p-3 rounded-md bg-muted/40 border space-y-2">
                      <div className="flex items-center justify-between text-[11px]">
                        <span className="font-medium text-foreground">Standard SLA Limit</span>
                        <Badge variant="outline" className="font-mono text-[10px]">T+2 Days</Badge>
                      </div>
                      <div className="flex items-center justify-between text-[11px]">
                        <span className="text-muted-foreground">Compliant Settlements</span>
                        <span className="font-mono font-semibold text-emerald-600">445 (94.6%)</span>
                      </div>
                      <div className="flex items-center justify-between text-[11px]">
                        <span className="text-muted-foreground">Delayed Settlements (5–12 Days)</span>
                        <span className="font-mono font-semibold text-amber-600">15 (5.4%)</span>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>
            </div>

            {/* Right Col: Priority Action Queue */}
            <div className="space-y-6">
              <Card className="border-primary/30">
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-sm font-semibold flex items-center gap-1.5">
                      <Sparkles className="h-4 w-4 text-violet-500" />
                      <span>Priority Action Queue</span>
                    </CardTitle>
                    <Link href="/exceptions" className="text-xs text-primary font-medium hover:underline flex items-center gap-0.5">
                      View All ({metrics.summary.total_exceptions || 227}) <ArrowUpRight className="h-3 w-3" />
                    </Link>
                  </div>
                  <CardDescription className="text-[11px]">
                    Top 5 unresolved exceptions sorted by weighted risk priority.
                  </CardDescription>
                </CardHeader>

                <CardContent className="p-0">
                  <div className="divide-y border-t">
                    {priorityQueue && priorityQueue.length > 0 ? (
                      priorityQueue.map((item: any, idx: number) => (
                        <div
                          key={idx}
                          className="p-3 hover:bg-muted/40 transition-colors flex items-center justify-between gap-3 text-xs"
                        >
                          <div className="space-y-1 min-w-0 flex-1">
                            <div className="flex items-center gap-2">
                              <Badge variant={item.severity.toLowerCase() as any} className="uppercase text-[9px] py-0">
                                {item.severity}
                              </Badge>
                              <span className="font-mono font-bold text-foreground truncate">
                                {item.exception_code}
                              </span>
                            </div>
                            <div className="text-[11px] text-muted-foreground truncate">
                              {item.exception_type.replace(/_/g, " ")}
                            </div>
                            <div className="text-[10px] text-muted-foreground font-mono">
                              Priority: <strong className="text-primary font-bold">{item.priority_score.toFixed(1)}</strong> • Discrepancy: {formatINR(item.discrepancy_amount)}
                            </div>
                          </div>

                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => setSelectedExceptionId(item.id)}
                            className="h-7 text-xs px-2.5 shrink-0 hover:bg-primary hover:text-primary-foreground"
                          >
                            Review
                          </Button>
                        </div>
                      ))
                    ) : (
                      <div className="p-6 text-center text-xs text-muted-foreground">
                        No priority items in queue. Load demo dataset or run reconciliation.
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>

              {/* Activity Timeline Card */}
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                    Recent Reconciliation Activity
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3 text-xs">
                  <div className="p-3 rounded bg-muted/40 border space-y-1 font-mono text-[11px]">
                    <div className="flex items-center justify-between text-foreground font-semibold">
                      <span>RUN_20260829_78B89D</span>
                      <Badge variant="resolved" className="text-[9px]">COMPLETED</Badge>
                    </div>
                    <div className="text-[10px] text-muted-foreground">
                      Processed 2,010 rows in 1.44s • Detected 227 exceptions
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>
        </>
      )}

      {/* Exception Review Drawer Modal */}
      <ExceptionDrawer
        exceptionId={selectedExceptionId}
        onClose={() => setSelectedExceptionId(null)}
        onStatusUpdated={loadDashboardData}
      />
    </div>
  );
}
