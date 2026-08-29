import React from "react";
import { BookOpen, CheckCircle, Cpu, FileCode } from "lucide-react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

export default function MethodologyPage() {
  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b pb-4">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-foreground flex items-center gap-2">
            Reconciliation Methodology & Rule Taxonomy
            <Badge variant="outline" className="font-mono text-[10px]">Track 4 Spec</Badge>
          </h1>
          <p className="text-xs text-muted-foreground mt-0.5">
            Technical architecture breakdown of vectorized matching algorithms, scikit-learn anomaly scoring, and 12-rule exception taxonomy.
          </p>
        </div>
      </div>

      <div className="space-y-4">
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-semibold flex items-center gap-2">
              <Cpu className="h-4 w-4 text-primary" />
              <span>Multi-Source Vectorized Matching Architecture</span>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-xs text-muted-foreground">
            <p>
              LedgerGuard AI ingests four distinct financial transaction feeds: Orders, Gateway Payments, Bank Settlement Batches (UTRs), and Vendor Billing Invoices.
            </p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-2">
              <div className="p-3 rounded border bg-card text-foreground space-y-1">
                <div className="font-semibold text-xs text-primary">1. Vectorized Pandas Matching</div>
                <p className="text-[11px] text-muted-foreground">Joins primary keys (<code className="font-mono">order_id</code>, <code className="font-mono">payment_id</code>, <code className="font-mono">utr</code>) across 500+ orders in &lt; 0.5s.</p>
              </div>
              <div className="p-3 rounded border bg-card text-foreground space-y-1">
                <div className="font-semibold text-xs text-violet-600 dark:text-violet-400">2. scikit-learn IsolationForest</div>
                <p className="text-[11px] text-muted-foreground">Trains MDR fee ratios per payment channel to highlight anomalous gateway charges.</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-semibold flex items-center gap-2">
              <FileCode className="h-4 w-4 text-emerald-600" />
              <span>12 Ground-Truth Exception Taxonomy</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs">
              {[
                "1. Missing Payment", "2. Payment Without Order", "3. Duplicate Payment",
                "4. Partial Payment", "5. Overpayment", "6. Settlement Mismatch",
                "7. Missing Settlement", "8. Delayed Settlement", "9. Duplicate Settlement",
                "10. Refund Mismatch", "11. Invoice Mismatch", "12. Fee Anomaly"
              ].map((rule, idx) => (
                <div key={idx} className="p-2.5 rounded bg-muted/40 border font-medium text-foreground">
                  {rule}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
