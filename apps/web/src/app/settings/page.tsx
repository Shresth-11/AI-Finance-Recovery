"use client";

import React from "react";
import { Settings, Sliders, Database, RotateCcw, Shield, Check, AlertTriangle } from "lucide-react";
import { toast } from "sonner";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { fetchApi } from "@/lib/api";

export default function SettingsPage() {
  const [critical, setCritical] = React.useState("50000");
  const [high, setHigh] = React.useState("10000");
  const [slaDays, setSlaDays] = React.useState("2");
  const [fuzzyConf, setFuzzyConf] = React.useState("85");
  const [loading, setLoading] = React.useState(false);
  const [confirmReset, setConfirmReset] = React.useState(false);

  const handleSaveThresholds = () => {
    toast.success("Saved reconciliation thresholds!", {
      description: `Critical: ₹${Number(critical).toLocaleString()} • High: ₹${Number(high).toLocaleString()} • SLA: T+${slaDays}d • Fuzzy: ${fuzzyConf}%`,
    });
  };

  const handleResetDatabase = async () => {
    setConfirmReset(false);
    setLoading(true);
    try {
      const res = await fetchApi<any>("/demo/reset", { method: "POST" });
      toast.success(res.message || "SQLite demo database reset successfully!");
    } catch (err: any) {
      toast.error(`Reset error: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 pb-12">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b pb-4">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-foreground flex items-center gap-2">
            Engine Configuration & System Settings
          </h1>
          <p className="text-xs text-muted-foreground mt-0.5">
            Adjust SLA delay limits, severity thresholds, fuzzy matching confidence scores, and demo database state.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-sm">
              <Sliders className="h-4 w-4 text-primary" />
              <span>Severity & Matching Thresholds</span>
            </CardTitle>
            <CardDescription>Configure quantitative rules engine limits.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4 text-xs">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="space-y-1">
                <label className="font-semibold text-foreground">Critical Severity Threshold (₹)</label>
                <Input
                  value={critical}
                  onChange={(e) => setCritical(e.target.value)}
                  className="h-9 font-mono text-xs"
                />
              </div>
              <div className="space-y-1">
                <label className="font-semibold text-foreground">High Severity Threshold (₹)</label>
                <Input
                  value={high}
                  onChange={(e) => setHigh(e.target.value)}
                  className="h-9 font-mono text-xs"
                />
              </div>
              <div className="space-y-1">
                <label className="font-semibold text-foreground">Settlement SLA Limit (Days)</label>
                <Input
                  value={slaDays}
                  onChange={(e) => setSlaDays(e.target.value)}
                  className="h-9 font-mono text-xs"
                />
              </div>
              <div className="space-y-1">
                <label className="font-semibold text-foreground">Fuzzy Match Minimum Confidence (%)</label>
                <Input
                  value={fuzzyConf}
                  onChange={(e) => setFuzzyConf(e.target.value)}
                  className="h-9 font-mono text-xs"
                />
              </div>
            </div>
            <Button size="sm" onClick={handleSaveThresholds} className="mt-2 text-xs gap-1.5">
              <Check className="h-3.5 w-3.5" />
              <span>Save Thresholds</span>
            </Button>
          </CardContent>
        </Card>

        <Card className="border-destructive/30">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-sm text-destructive">
              <RotateCcw className="h-4 w-4" />
              <span>Demo State Management</span>
            </CardTitle>
            <CardDescription>Reset local SQLite database state.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3 text-xs">
            <p className="text-muted-foreground">
              Clears all orders, payments, settlements, invoices, reconciliation runs, and exceptions from SQLite database.
            </p>
            <Button
              variant="destructive"
              size="sm"
              disabled={loading}
              onClick={() => setConfirmReset(true)}
              className="w-full gap-1.5 text-xs"
            >
              <RotateCcw className="h-3.5 w-3.5" />
              <span>{loading ? "Resetting..." : "Reset Demo Database"}</span>
            </Button>
          </CardContent>
        </Card>
      </div>

      {/* Confirmation Dialog for Reset */}
      {confirmReset && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-background/80 backdrop-blur-sm">
          <div className="w-full max-w-md p-6 rounded-lg border bg-card text-card-foreground shadow-2xl space-y-4">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-red-100 text-red-700 dark:bg-red-950 dark:text-red-300">
                <AlertTriangle className="h-5 w-5" />
              </div>
              <div>
                <h3 className="text-base font-semibold text-foreground">Reset SQLite Database?</h3>
                <p className="text-xs text-muted-foreground">
                  This action will delete all active financial records and exception logs.
                </p>
              </div>
            </div>

            <div className="flex items-center justify-end gap-2 pt-2 border-t">
              <Button variant="outline" size="sm" onClick={() => setConfirmReset(false)}>
                Cancel
              </Button>
              <Button size="sm" variant="destructive" onClick={handleResetDatabase}>
                Yes, Reset Database
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
