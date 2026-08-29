"use client";

import * as React from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import {
  ArrowLeft,
  ShieldAlert,
  Bot,
  CheckCircle,
  AlertTriangle,
  Clock,
  ExternalLink,
  FileText,
  Send,
  Sparkles,
  GitCommit,
  UserCheck,
  Building,
  HelpCircle,
  Check,
  X,
  RotateCcw,
  ShieldCheck,
  ChevronRight,
} from "lucide-react";
import { toast } from "sonner";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { formatINR, formatDate } from "@/lib/utils";
import { fetchApi } from "@/lib/api";

export default function ExceptionDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = params?.id as string;

  const [data, setData] = React.useState<any>(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);
  const [updating, setUpdating] = React.useState(false);
  const [actionNote, setActionNote] = React.useState("");

  // Confirmation Modal State
  const [pendingStatus, setPendingStatus] = React.useState<string | null>(null);

  const loadDetail = React.useCallback(async () => {
    if (!id) return;
    setLoading(true);
    setError(null);
    try {
      const res = await fetchApi<any>(`/exceptions/${id}`);
      setData(res);
    } catch (err: any) {
      setError(err.message || `Failed to load exception #${id}`);
    } finally {
      setLoading(false);
    }
  }, [id]);

  React.useEffect(() => {
    loadDetail();
  }, [loadDetail]);

  const handleConfirmStatusUpdate = async () => {
    if (!pendingStatus) return;
    setUpdating(true);
    try {
      await fetchApi(`/exceptions/${id}/status`, {
        method: "PATCH",
        body: JSON.stringify({
          status: pendingStatus,
          resolution_code: pendingStatus === "RESOLVED" ? "OFFICER_APPROVED" : "OFFICER_ACTION",
          note: actionNote || `Status updated to ${pendingStatus} by Finance Officer`,
          performed_by: "Finance Officer",
        }),
      });

      toast.success(`Exception status updated to ${pendingStatus}!`, {
        description: "Audit trail log entry recorded in backend database.",
      });

      setPendingStatus(null);
      setActionNote("");
      await loadDetail();
    } catch (err: any) {
      toast.error(`Update failed: ${err.message}`);
    } finally {
      setUpdating(false);
    }
  };

  // Compute visual reconciliation lifecycle timeline steps
  const getLifecycleSteps = () => {
    if (!data) return [];
    const hasOrder = !!data.order_id;
    const hasPayment = !!data.payment_id;
    const hasSettlement = !!data.settlement_id;
    const isMissingSettlement = data.exception_type === "MISSING_SETTLEMENT";

    return [
      { name: "Order Created", status: hasOrder ? "complete" : "inactive", detail: data.order_id ? `Ord #${data.order_id}` : "N/A" },
      { name: "Payment Captured", status: hasPayment ? "complete" : "inactive", detail: data.payment_id ? `Pay #${data.payment_id}` : "N/A" },
      { name: "Settlement Expected", status: "complete", detail: "T+2 Payout Window" },
      { name: "Bank Payout", status: hasSettlement ? "complete" : isMissingSettlement ? "failed" : "warning", detail: data.settlement_id ? `UTR: ${data.related_settlement?.utr || data.settlement_id}` : "Payout Gap" },
      { name: "Exception Flagged", status: "flagged", detail: data.exception_code },
    ];
  };

  const lifecycleSteps = getLifecycleSteps();

  return (
    <div className="space-y-6 pb-16">
      {/* Top Header Navigation */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b pb-4">
        <div className="flex items-center gap-3">
          <Link href="/exceptions">
            <Button variant="ghost" size="icon" className="h-9 w-9 border" aria-label="Back to exceptions queue">
              <ArrowLeft className="h-4 w-4" />
            </Button>
          </Link>
          <div>
            <div className="flex items-center gap-2.5">
              <h1 className="text-xl font-bold tracking-tight text-foreground font-mono">
                {data?.exception_code || `EXC_${id}`}
              </h1>
              {data?.severity && (
                <Badge variant={data.severity.toLowerCase() as any} className="uppercase text-[10px] font-bold">
                  ● {data.severity}
                </Badge>
              )}
              {data?.status && (
                <Badge variant={data.status === "RESOLVED" ? "resolved" : "outline"} className="text-[10px] uppercase font-semibold">
                  {data.status}
                </Badge>
              )}
            </div>
            <p className="text-xs text-muted-foreground mt-0.5">
              Incident Investigation • Detected: {data?.created_at ? formatDate(data.created_at) : "N/A"}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Badge variant="outline" className="font-mono text-xs px-2.5 py-1">
            Priority Score: <strong className="text-primary font-bold ml-1">{data?.priority_score?.toFixed(1) || "85.0"} / 100</strong>
          </Badge>
          <Button variant="outline" size="sm" onClick={() => router.push("/exceptions")} className="text-xs">
            Queue View
          </Button>
        </div>
      </div>

      {loading && (
        <div className="flex flex-col items-center justify-center py-20 text-muted-foreground space-y-3">
          <div className="h-6 w-6 animate-spin rounded-full border-2 border-primary border-t-transparent" />
          <p className="text-xs">Fetching incident evidence cards and audit logs...</p>
        </div>
      )}

      {error && (
        <Card className="border-destructive/30 bg-destructive/5">
          <CardContent className="p-8 text-center space-y-3">
            <AlertTriangle className="h-8 w-8 text-destructive mx-auto" />
            <h3 className="text-base font-semibold text-foreground">Exception Record Not Found</h3>
            <p className="text-xs text-muted-foreground">{error}</p>
            <Button size="sm" variant="outline" onClick={() => router.push("/exceptions")}>
              Return to Exceptions Queue
            </Button>
          </CardContent>
        </Card>
      )}

      {data && !loading && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Panel (Left 2/3): Financial Discrepancy, Lifecycle, Comparison, Rules & Audit */}
          <div className="lg:col-span-2 space-y-6">
            {/* Prominent Discrepancy Amount Card */}
            <Card className="border-amber-200 bg-amber-50/20 dark:border-amber-900/40 dark:bg-amber-950/10">
              <CardContent className="p-5 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                <div>
                  <span className="text-xs font-semibold uppercase tracking-wider text-amber-700 dark:text-amber-400">
                    Discrepancy Amount at Risk
                  </span>
                  <div className="text-3xl font-extrabold tabular-nums text-amber-800 dark:text-amber-300 mt-0.5">
                    {formatINR(data.discrepancy_amount)}
                  </div>
                  <p className="text-xs text-amber-700 dark:text-amber-400 mt-1">
                    Category: <strong className="font-semibold">{data.exception_type.replace(/_/g, " ")}</strong>
                  </p>
                </div>
                <div className="text-left sm:text-right border-t sm:border-t-0 sm:border-l pt-3 sm:pt-0 sm:pl-4">
                  <div className="text-xs text-muted-foreground">Match Confidence</div>
                  <div className="text-xl font-bold font-mono text-emerald-600 dark:text-emerald-400 mt-0.5">
                    {data.ai_confidence_score ? `${(data.ai_confidence_score * 100).toFixed(0)}%` : "95%"}
                  </div>
                  <span className="text-[10px] text-muted-foreground font-mono">Method: {data.match_method || "EXACT_ID"}</span>
                </div>
              </CardContent>
            </Card>

            {/* Visual Reconciliation Lifecycle Timeline */}
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Reconciliation Lifecycle Flow
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2 text-xs">
                  {lifecycleSteps.map((step, idx) => (
                    <React.Fragment key={idx}>
                      <div className="flex items-center gap-2">
                        <div
                          className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-xs font-bold ${
                            step.status === "complete"
                              ? "bg-emerald-100 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300"
                              : step.status === "failed"
                              ? "bg-red-100 text-red-700 dark:bg-red-950 dark:text-red-300"
                              : step.status === "flagged"
                              ? "bg-amber-100 text-amber-700 dark:bg-amber-950 dark:text-amber-300"
                              : "bg-muted text-muted-foreground"
                          }`}
                        >
                          {step.status === "complete" ? (
                            <Check className="h-4 w-4" />
                          ) : step.status === "failed" ? (
                            <X className="h-4 w-4" />
                          ) : step.status === "flagged" ? (
                            <AlertTriangle className="h-4 w-4" />
                          ) : (
                            idx + 1
                          )}
                        </div>
                        <div>
                          <div className="font-semibold text-foreground">{step.name}</div>
                          <div className="text-[10px] text-muted-foreground font-mono">{step.detail}</div>
                        </div>
                      </div>
                      {idx < lifecycleSteps.length - 1 && (
                        <ChevronRight className="hidden sm:block h-4 w-4 text-muted-foreground shrink-0" />
                      )}
                    </React.Fragment>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Side-by-Side Financial Comparison Grid */}
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Side-by-Side Record Matrix (Order vs Payment vs Settlement vs Invoice)
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 text-xs">
                  {/* Order Entity */}
                  <div className={`p-3 rounded-lg border bg-card space-y-2 ${data.related_order ? "border-primary/40" : "border-dashed opacity-60"}`}>
                    <div className="flex items-center justify-between border-b pb-1">
                      <span className="font-bold text-foreground">1. Order</span>
                      <Badge variant="outline" className="text-[9px]">ERP</Badge>
                    </div>
                    {data.related_order ? (
                      <div className="space-y-1 text-[11px]">
                        <div><span className="text-muted-foreground">ID:</span> <code className="font-mono text-foreground font-semibold">{data.related_order.order_id}</code></div>
                        <div><span className="text-muted-foreground">Amount:</span> <strong className="font-mono text-foreground">{formatINR(data.related_order.amount)}</strong></div>
                        <div><span className="text-muted-foreground">Customer:</span> <span className="truncate block text-foreground">{data.related_order.customer_name}</span></div>
                        <div><span className="text-muted-foreground">Status:</span> <span className="font-semibold text-emerald-600">{data.related_order.status}</span></div>
                      </div>
                    ) : (
                      <div className="text-[11px] text-muted-foreground italic py-2">No matching order record</div>
                    )}
                  </div>

                  {/* Payment Entity */}
                  <div className={`p-3 rounded-lg border bg-card space-y-2 ${data.related_payment ? "border-primary/40" : "border-dashed opacity-60"}`}>
                    <div className="flex items-center justify-between border-b pb-1">
                      <span className="font-bold text-foreground">2. Payment</span>
                      <Badge variant="outline" className="text-[9px]">Gateway</Badge>
                    </div>
                    {data.related_payment ? (
                      <div className="space-y-1 text-[11px]">
                        <div><span className="text-muted-foreground">ID:</span> <code className="font-mono text-foreground font-semibold">{data.related_payment.payment_id}</code></div>
                        <div><span className="text-muted-foreground">Captured:</span> <strong className="font-mono text-foreground">{formatINR(data.related_payment.amount)}</strong></div>
                        <div><span className="text-muted-foreground">Fee (MDR):</span> <span className="font-mono text-muted-foreground">{formatINR(data.related_payment.fee_amount || 0)}</span></div>
                        <div><span className="text-muted-foreground">Method:</span> <span className="font-semibold text-foreground">{data.related_payment.method}</span></div>
                      </div>
                    ) : (
                      <div className="text-[11px] text-muted-foreground italic py-2">No matching payment record</div>
                    )}
                  </div>

                  {/* Settlement Entity */}
                  <div className={`p-3 rounded-lg border bg-card space-y-2 ${data.related_settlement ? "border-primary/40" : "border-dashed border-red-300 bg-red-50/10 opacity-80"}`}>
                    <div className="flex items-center justify-between border-b pb-1">
                      <span className="font-bold text-foreground">3. Settlement</span>
                      <Badge variant="outline" className="text-[9px]">Bank UTR</Badge>
                    </div>
                    {data.related_settlement ? (
                      <div className="space-y-1 text-[11px]">
                        <div><span className="text-muted-foreground">ID:</span> <code className="font-mono text-foreground font-semibold">{data.related_settlement.settlement_id}</code></div>
                        <div><span className="text-muted-foreground">Net Payout:</span> <strong className="font-mono text-emerald-600">{formatINR(data.related_settlement.net_amount)}</strong></div>
                        <div><span className="text-muted-foreground">UTR:</span> <code className="font-mono text-[10px] text-foreground">{data.related_settlement.utr}</code></div>
                        <div><span className="text-muted-foreground">Status:</span> <span className="font-semibold text-emerald-600">{data.related_settlement.status}</span></div>
                      </div>
                    ) : (
                      <div className="text-[11px] text-red-600 dark:text-red-400 font-semibold py-2">⚠ Missing Settlement Entry</div>
                    )}
                  </div>

                  {/* Invoice Entity */}
                  <div className={`p-3 rounded-lg border bg-card space-y-2 ${data.related_invoice ? "border-primary/40" : "border-dashed opacity-60"}`}>
                    <div className="flex items-center justify-between border-b pb-1">
                      <span className="font-bold text-foreground">4. Invoice</span>
                      <Badge variant="outline" className="text-[9px]">Tax Invoice</Badge>
                    </div>
                    {data.related_invoice ? (
                      <div className="space-y-1 text-[11px]">
                        <div><span className="text-muted-foreground">ID:</span> <code className="font-mono text-foreground font-semibold">{data.related_invoice.invoice_id}</code></div>
                        <div><span className="text-muted-foreground">Total:</span> <strong className="font-mono text-foreground">{formatINR(data.related_invoice.total_amount)}</strong></div>
                        <div><span className="text-muted-foreground">GST:</span> <span className="font-mono text-muted-foreground">{formatINR(data.related_invoice.gst_amount || 0)}</span></div>
                        <div><span className="text-muted-foreground">Status:</span> <span className="font-semibold text-foreground">{data.related_invoice.status}</span></div>
                      </div>
                    ) : (
                      <div className="text-[11px] text-muted-foreground italic py-2">No matching invoice record</div>
                    )}
                  </div>
                </div>

                {/* Structured Evidence Key-Value Pairs */}
                {data.evidence?.side_by_side && (
                  <div className="space-y-1.5 border-t pt-3">
                    <span className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
                      Field Variance Analysis
                    </span>
                    <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 text-[11px]">
                      {Object.entries(data.evidence.side_by_side).map(([k, v]: any, idx) => (
                        <div key={idx} className="p-2 rounded bg-muted/40 border font-mono">
                          <div className="text-[10px] text-muted-foreground">{k}</div>
                          <div className="font-semibold text-foreground truncate">{String(v)}</div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* "Why Was This Flagged?" & Rule Trigger Info */}
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Why Was This Flagged? (Triggered Deterministic Rules)
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3 text-xs">
                <div className="p-3 rounded bg-muted/40 border space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-foreground font-mono text-xs">
                      RULE_{data.exception_type}
                    </span>
                    <Badge variant={data.severity.toLowerCase() as any} className="uppercase text-[10px]">
                      {data.severity}
                    </Badge>
                  </div>
                  <p className="text-muted-foreground text-xs leading-relaxed">
                    {data.evidence?.summary || "Rule-based engine identified variance beyond configured tolerance limit."}
                  </p>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-[11px]">
                  <div className="p-2.5 rounded border bg-card space-y-0.5">
                    <span className="text-muted-foreground">Match Algorithm</span>
                    <div className="font-mono font-semibold text-foreground">{data.match_method || "Vectorized Exact Match"}</div>
                  </div>
                  <div className="p-2.5 rounded border bg-card space-y-0.5">
                    <span className="text-muted-foreground">Confidence Score</span>
                    <div className="font-mono font-semibold text-emerald-600">{data.ai_confidence_score ? `${(data.ai_confidence_score * 100).toFixed(0)}%` : "95%"}</div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Real Backend Audit Timeline */}
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Audit Trail & Governance Logs ({data.audit_history?.length || 0})
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3 text-xs">
                {data.audit_history && data.audit_history.length > 0 ? (
                  <div className="space-y-2 border-l-2 border-primary/30 pl-4 ml-1">
                    {data.audit_history.map((a: any, idx: number) => (
                      <div key={idx} className="relative space-y-1">
                        <div className="absolute -left-[21px] top-1 h-2.5 w-2.5 rounded-full bg-primary" />
                        <div className="flex items-center justify-between">
                          <span className="font-semibold text-foreground">{a.action}</span>
                          <span className="text-[10px] text-muted-foreground font-mono">{formatDate(a.timestamp)}</span>
                        </div>
                        <p className="text-[11px] text-muted-foreground">{a.reason || "Action performed"}</p>
                        <div className="text-[10px] text-muted-foreground font-mono">By: {a.performed_by}</div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center text-muted-foreground py-4 italic">No prior status updates logged.</div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Right Panel (1/3): AI Analysis Card & Status Actions */}
          <div className="space-y-6">
            {/* LedgerGuard AI Analysis Card */}
            <Card className="border-violet-200 dark:border-violet-900/50 bg-violet-50/10">
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-semibold flex items-center gap-2 text-violet-700 dark:text-violet-300">
                  <Sparkles className="h-4 w-4" />
                  <span>LedgerGuard Analysis</span>
                </CardTitle>
                <CardDescription className="text-[10px] text-violet-600 dark:text-violet-400 font-semibold">
                  ⚠ AI-assisted explanation — requires human officer review. AI never takes automated financial actions.
                </CardDescription>
              </CardHeader>

              <CardContent className="space-y-3 text-xs">
                {/* Summary */}
                <div className="space-y-1">
                  <span className="font-semibold text-foreground uppercase text-[10px] tracking-wider">Summary</span>
                  <p className="text-muted-foreground text-[11px] leading-relaxed">
                    {data.evidence?.summary || "Discrepancy identified between captured transaction ledger and bank settlement advice."}
                  </p>
                </div>

                {/* Evidence */}
                <div className="space-y-1 border-t pt-2">
                  <span className="font-semibold text-foreground uppercase text-[10px] tracking-wider">Cited Evidence</span>
                  <div className="font-mono text-[11px] text-primary space-y-0.5">
                    {data.order_id && <div>Order Ref: ord_live_{data.order_id}</div>}
                    {data.payment_id && <div>Payment Ref: pay_live_{data.payment_id}</div>}
                    {data.settlement_id && <div>Settlement Ref: set_live_{data.settlement_id}</div>}
                  </div>
                </div>

                {/* Likely Cause */}
                <div className="space-y-1 border-t pt-2">
                  <span className="font-semibold text-foreground uppercase text-[10px] tracking-wider">Likely Cause</span>
                  <p className="text-muted-foreground text-[11px]">
                    {data.exception_type === "DUPLICATE_PAYMENT"
                      ? "Duplicate checkout submit triggered double payment captures."
                      : data.exception_type === "MISSING_SETTLEMENT"
                      ? "Bank payout batch window exceeded T+2 SLA delay threshold."
                      : "MDR fee rate overcharged beyond agreed merchant contract."}
                  </p>
                </div>

                {/* Suggested Remediation */}
                {data.evidence?.remediation && (
                  <div className="space-y-1 border-t pt-2">
                    <span className="font-semibold text-foreground uppercase text-[10px] tracking-wider">Suggested Next Step</span>
                    <p className="text-emerald-700 dark:text-emerald-300 text-[11px] font-medium">
                      {data.evidence.remediation}
                    </p>
                  </div>
                )}

                {/* Suggested Team Owner */}
                <div className="space-y-1 border-t pt-2 flex items-center justify-between text-[11px]">
                  <span className="text-muted-foreground">Assigned Owner / Team</span>
                  <Badge variant="outline" className="font-mono text-[10px]">Payment Ops Team</Badge>
                </div>
              </CardContent>
            </Card>

            {/* Status Review Actions Card */}
            <Card className="border-primary/40">
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-semibold">Incident Resolution Actions</CardTitle>
                <CardDescription className="text-[11px]">Human-in-the-Loop decision controls.</CardDescription>
              </CardHeader>

              <CardContent className="space-y-3 text-xs">
                <div className="grid grid-cols-2 gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={updating}
                    onClick={() => setPendingStatus("INVESTIGATING")}
                    className="text-xs"
                  >
                    Investigating
                  </Button>

                  <Button
                    variant="outline"
                    size="sm"
                    disabled={updating}
                    onClick={() => setPendingStatus("IGNORED")}
                    className="text-xs text-muted-foreground"
                  >
                    Mark Ignored
                  </Button>

                  <Button
                    variant="destructive"
                    size="sm"
                    disabled={updating}
                    onClick={() => setPendingStatus("ESCALATED")}
                    className="text-xs col-span-1"
                  >
                    Escalate
                  </Button>

                  <Button
                    size="sm"
                    disabled={updating}
                    onClick={() => setPendingStatus("RESOLVED")}
                    className="text-xs bg-emerald-600 hover:bg-emerald-700 text-white col-span-1"
                  >
                    Resolve
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      )}

      {/* Mandatory Confirmation Modal Dialog for Status Changes */}
      {pendingStatus && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-background/80 backdrop-blur-sm">
          <div className="w-full max-w-md p-6 rounded-lg border bg-card text-card-foreground shadow-2xl space-y-4">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary/10 text-primary">
                <ShieldCheck className="h-5 w-5" />
              </div>
              <div>
                <h3 className="text-base font-semibold text-foreground">
                  Confirm Status Change to {pendingStatus}
                </h3>
                <p className="text-xs text-muted-foreground">
                  This decision will be recorded in the backend database audit log.
                </p>
              </div>
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-foreground">Resolution Note / Reason (Optional)</label>
              <textarea
                rows={2}
                value={actionNote}
                onChange={(e) => setActionNote(e.target.value)}
                placeholder="Enter approval note, refund ticket ID, or escalation details..."
                className="w-full rounded-md border border-input bg-background p-2 text-xs outline-none focus:ring-1 focus:ring-ring"
              />
            </div>

            <div className="flex items-center justify-end gap-2 pt-2 border-t">
              <Button variant="outline" size="sm" onClick={() => setPendingStatus(null)}>
                Cancel
              </Button>
              <Button
                size="sm"
                disabled={updating}
                onClick={handleConfirmStatusUpdate}
                className="bg-primary text-primary-foreground"
              >
                {updating ? "Saving..." : "Confirm & Update Status"}
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
