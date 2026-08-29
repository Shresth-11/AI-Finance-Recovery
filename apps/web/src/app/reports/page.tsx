"use client";

import React from "react";
import { FileSpreadsheet, Download, Calendar, CheckCircle, Database } from "lucide-react";
import { toast } from "sonner";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { getExportCsvUrl } from "@/lib/api";

export default function ReportsPage() {
  const handleExportAllExceptions = () => {
    const url = getExportCsvUrl();
    window.open(url, "_blank");
    toast.info("Downloading complete exception audit report CSV...");
  };

  const handleExportCriticalOnly = () => {
    const url = getExportCsvUrl({ severity: "CRITICAL" });
    window.open(url, "_blank");
    toast.info("Downloading critical severity exceptions CSV...");
  };

  const handleExportFeeAnomalies = () => {
    const url = getExportCsvUrl({ exception_type: "FEE_ANOMALY" });
    window.open(url, "_blank");
    toast.info("Downloading gateway MDR fee claim sheet CSV...");
  };

  return (
    <div className="space-y-6 pb-12">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b pb-4">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-foreground flex items-center gap-2">
            Financial Reports & Compliance Exports
          </h1>
          <p className="text-xs text-muted-foreground mt-0.5">
            Export structured reconciliation summaries, exception audit trails, and gateway settlement ledgers.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Report 1 */}
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-semibold">Complete Exception Audit Report</CardTitle>
            <CardDescription className="text-xs">
              Comprehensive CSV export of all detected financial exceptions with severity and priority scores.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="p-3 rounded bg-muted/40 text-xs text-muted-foreground space-y-1">
              <div>• Includes all 12 exception categories</div>
              <div>• Includes side-by-side evidence summaries and UTR references</div>
            </div>
            <Button size="sm" onClick={handleExportAllExceptions} className="gap-1.5 text-xs w-full">
              <Download className="h-3.5 w-3.5" />
              <span>Download Exceptions CSV</span>
            </Button>
          </CardContent>
        </Card>

        {/* Report 2 */}
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-semibold text-red-700 dark:text-red-400">
              Critical Risk Exceptions Audit
            </CardTitle>
            <CardDescription className="text-xs">
              Filtered CSV report of urgent duplicate charges and severe discrepancies.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="p-3 rounded bg-muted/40 text-xs text-muted-foreground space-y-1">
              <div>• Filtered for CRITICAL severity items</div>
              <div>• Duplicate payments & overpayment refund ticket list</div>
            </div>
            <Button size="sm" variant="destructive" onClick={handleExportCriticalOnly} className="gap-1.5 text-xs w-full">
              <Download className="h-3.5 w-3.5" />
              <span>Download Critical CSV</span>
            </Button>
          </CardContent>
        </Card>

        {/* Report 3 */}
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-semibold text-violet-700 dark:text-violet-300">
              Gateway Fee Discrepancy Statement
            </CardTitle>
            <CardDescription className="text-xs">
              Statement of anomalous gateway MDR charges and fee overcharge claims.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="p-3 rounded bg-muted/40 text-xs text-muted-foreground space-y-1">
              <div>• Isolated MDR fee overcharges against standard contract rates</div>
              <div>• Claim ticket references for payment gateway reconciliation</div>
            </div>
            <Button variant="outline" size="sm" onClick={handleExportFeeAnomalies} className="gap-1.5 text-xs w-full">
              <FileSpreadsheet className="h-3.5 w-3.5 text-violet-600" />
              <span>Export Gateway MDR Claim Sheet</span>
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
