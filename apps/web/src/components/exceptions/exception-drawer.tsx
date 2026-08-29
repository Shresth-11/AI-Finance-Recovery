"use client";

import * as React from "react";
import {
  X,
  ShieldAlert,
  Bot,
  CheckCircle,
  XCircle,
  Clock,
  ExternalLink,
  FileText,
  AlertTriangle,
  Send,
} from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { formatINR, formatDate } from "@/lib/utils";
import { fetchApi } from "@/lib/api";

interface ExceptionDrawerProps {
  exceptionId: number | string | null;
  onClose: () => void;
  onStatusUpdated?: () => void;
}

export function ExceptionDrawer({
  exceptionId,
  onClose,
  onStatusUpdated,
}: ExceptionDrawerProps) {
  const [data, setData] = React.useState<any>(null);
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [updating, setUpdating] = React.useState(false);
  const [actionNote, setActionNote] = React.useState("");

  React.useEffect(() => {
    if (!exceptionId) return;

    const loadDetail = async () => {
      setLoading(true);
      setError(null);
      try {
        const detail = await fetchApi<any>(`/exceptions/${exceptionId}`);
        setData(detail);
      } catch (err: any) {
        setError(err.message || "Failed to load exception details");
      } finally {
        setLoading(false);
      }
    };

    loadDetail();
  }, [exceptionId]);

  if (!exceptionId) return null;

  const handleUpdateStatus = async (newStatus: string) => {
    setUpdating(true);
    try {
      await fetchApi(`/exceptions/${exceptionId}/status`, {
        method: "PATCH",
        body: JSON.stringify({
          status: newStatus,
          resolution_code: newStatus === "RESOLVED" ? "OFFICER_APPROVED" : "OFFICER_REJECTED",
          note: actionNote || `Status changed to ${newStatus} by Finance Officer`,
          performed_by: "Finance Officer",
        }),
      });

      toast.success(`Exception ${data?.exception_code || `EXC_${exceptionId}`} marked as ${newStatus.toLowerCase()}.`);
      if (onStatusUpdated) onStatusUpdated();
      onClose();
    } catch (err: any) {
      toast.error(`Update failed: ${err.message}`);
    } finally {
      setUpdating(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-background/80 backdrop-blur-sm animate-in fade-in-0">
      <div className="fixed inset-0" onClick={onClose} />
      <div className="relative w-full max-w-2xl h-full border-l bg-card text-card-foreground shadow-2xl overflow-y-auto z-50 flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b bg-muted/30">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary/10 text-primary">
              <ShieldAlert className="h-5 w-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-mono font-bold text-base text-foreground">
                  {data?.exception_code || `EXC_${exceptionId}`}
                </span>
                {data?.severity && (
                  <Badge variant={data.severity.toLowerCase() as any} className="uppercase text-[10px]">
                    {data.severity}
                  </Badge>
                )}
                {data?.status && (
                  <Badge variant="outline" className="text-[10px]">
                    {data.status}
                  </Badge>
                )}
              </div>
              <p className="text-xs text-muted-foreground mt-0.5">
                {data?.exception_type ? data.exception_type.replace(/_/g, " ") : "Exception Detail Review"}
              </p>
            </div>
          </div>
          <Button variant="ghost" size="icon" onClick={onClose} aria-label="Close drawer">
            <X className="h-4 w-4" />
          </Button>
        </div>

        {/* Content Body */}
        <div className="flex-1 p-6 space-y-6">
          {loading && (
            <div className="flex flex-col items-center justify-center py-20 text-muted-foreground space-y-3">
              <div className="h-6 w-6 animate-spin rounded-full border-2 border-primary border-t-transparent" />
              <p className="text-xs">Fetching evidence payload and audit history...</p>
            </div>
          )}

          {error && (
            <div className="p-4 rounded-lg bg-destructive/10 text-destructive text-xs space-y-2 border border-destructive/20">
              <div className="font-semibold flex items-center gap-1.5">
                <AlertTriangle className="h-4 w-4" />
                <span>Error Loading Detail</span>
              </div>
              <p>{error}</p>
            </div>
          )}

          {data && !loading && (
            <>
              {/* Financial Discrepancy Card */}
              <div className="grid grid-cols-3 gap-3 p-4 rounded-lg bg-muted/40 border text-xs">
                <div>
                  <span className="text-muted-foreground text-[11px]">Discrepancy Amount</span>
                  <div className="font-bold text-base tabular-nums text-foreground mt-0.5">
                    {formatINR(data.discrepancy_amount)}
                  </div>
                </div>
                <div>
                  <span className="text-muted-foreground text-[11px]">Priority Score</span>
                  <div className="font-bold text-base tabular-nums text-primary mt-0.5">
                    {data.priority_score ? `${data.priority_score.toFixed(1)} / 100` : "85.0"}
                  </div>
                </div>
                <div>
                  <span className="text-muted-foreground text-[11px]">AI Confidence</span>
                  <div className="font-bold text-base tabular-nums text-emerald-600 dark:text-emerald-400 mt-0.5">
                    {data.ai_confidence_score ? `${(data.ai_confidence_score * 100).toFixed(0)}%` : "95%"}
                  </div>
                </div>
              </div>

              {/* Evidence Card & Side-by-Side Comparison */}
              <Card className="border-violet-200 dark:border-violet-900/50 bg-violet-50/10">
                <CardHeader className="py-3 px-4">
                  <CardTitle className="text-xs font-semibold flex items-center gap-2 text-violet-700 dark:text-violet-300">
                    <Bot className="h-4 w-4" />
                    <span>Evidence Summary & AI Explanation</span>
                  </CardTitle>
                </CardHeader>
                <CardContent className="px-4 pb-4 space-y-3 text-xs">
                  <p className="text-foreground leading-relaxed font-medium">
                    {data.evidence?.summary || "Structured evidence details generated by reconciliation rules engine."}
                  </p>

                  {/* Side-by-Side Comparison Card */}
                  {data.evidence?.side_by_side && (
                    <div className="space-y-1.5 border-t pt-2 mt-2">
                      <span className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
                        Side-by-Side Comparison Card
                      </span>
                      <div className="grid grid-cols-2 gap-2 text-[11px]">
                        {Object.entries(data.evidence.side_by_side).map(([k, v]: any, idx) => (
                          <div key={idx} className="p-2 rounded bg-card border font-mono">
                            <div className="text-[10px] text-muted-foreground">{k}</div>
                            <div className="font-semibold text-foreground truncate">{String(v)}</div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Proposed Remediation Action */}
                  {data.evidence?.remediation && (
                    <div className="p-3 rounded bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-900/50 space-y-1 text-emerald-800 dark:text-emerald-300 text-[11px]">
                      <div className="font-semibold flex items-center gap-1.5">
                        <CheckCircle className="h-3.5 w-3.5" />
                        <span>Recommended Remediation Step:</span>
                      </div>
                      <p>{data.evidence.remediation}</p>
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Related Financial Records Tabs */}
              <div className="space-y-2">
                <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Related Entity Records
                </h4>
                <div className="space-y-2 text-xs">
                  {data.related_order && (
                    <div className="p-3 rounded border bg-card flex justify-between items-center">
                      <div>
                        <div className="font-semibold text-foreground">Order #{data.related_order.order_id}</div>
                        <div className="text-muted-foreground text-[11px]">
                          {data.related_order.customer_name} • {data.related_order.customer_email}
                        </div>
                      </div>
                      <div className="text-right font-mono tabular-nums font-semibold">
                        {formatINR(data.related_order.amount)}
                      </div>
                    </div>
                  )}

                  {data.related_payment && (
                    <div className="p-3 rounded border bg-card flex justify-between items-center">
                      <div>
                        <div className="font-semibold text-foreground">Payment #{data.related_payment.payment_id}</div>
                        <div className="text-muted-foreground text-[11px]">
                          Method: {data.related_payment.method} • Ref: {data.related_payment.gateway_ref || "N/A"}
                        </div>
                      </div>
                      <div className="text-right font-mono tabular-nums font-semibold">
                        {formatINR(data.related_payment.amount)}
                      </div>
                    </div>
                  )}

                  {data.related_settlement && (
                    <div className="p-3 rounded border bg-card flex justify-between items-center">
                      <div>
                        <div className="font-semibold text-foreground">Settlement #{data.related_settlement.settlement_id}</div>
                        <div className="text-muted-foreground text-[11px]">
                          UTR: <code className="font-mono text-[10px]">{data.related_settlement.utr}</code>
                        </div>
                      </div>
                      <div className="text-right font-mono tabular-nums font-semibold text-emerald-600">
                        {formatINR(data.related_settlement.net_amount)}
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {/* Audit History Timeline */}
              {data.audit_history && data.audit_history.length > 0 && (
                <div className="space-y-2 border-t pt-4">
                  <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                    Audit Trail & History ({data.audit_history.length})
                  </h4>
                  <div className="space-y-2">
                    {data.audit_history.map((a: any, idx: number) => (
                      <div key={idx} className="p-2.5 rounded bg-muted/30 border text-xs space-y-1">
                        <div className="flex items-center justify-between">
                          <span className="font-semibold text-foreground">{a.action}</span>
                          <span className="text-[10px] text-muted-foreground">{formatDate(a.timestamp)}</span>
                        </div>
                        <p className="text-[11px] text-muted-foreground">{a.reason || "Action performed"}</p>
                        <div className="text-[10px] text-muted-foreground font-mono">By: {a.performed_by}</div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Action Note Input & Decision Buttons */}
              <div className="border-t pt-4 space-y-3">
                <div className="space-y-1">
                  <label className="text-xs font-semibold text-foreground">Finance Officer Note / Resolution Reason</label>
                  <input
                    type="text"
                    value={actionNote}
                    onChange={(e) => setActionNote(e.target.value)}
                    placeholder="Enter resolution notes, refund reference ticket, or claim ID..."
                    className="w-full h-9 rounded-md border border-input bg-background px-3 text-xs outline-none focus:ring-1 focus:ring-ring"
                  />
                </div>

                <div className="flex items-center justify-end gap-2 pt-2">
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={updating}
                    onClick={() => handleUpdateStatus("IGNORED")}
                    className="text-xs"
                  >
                    Mark Ignored
                  </Button>
                  <Button
                    variant="destructive"
                    size="sm"
                    disabled={updating}
                    onClick={() => handleUpdateStatus("ESCALATED")}
                    className="text-xs"
                  >
                    Escalate
                  </Button>
                  <Button
                    size="sm"
                    disabled={updating}
                    onClick={() => handleUpdateStatus("RESOLVED")}
                    className="gap-1 text-xs bg-emerald-600 hover:bg-emerald-700 text-white"
                  >
                    <CheckCircle className="h-3.5 w-3.5" />
                    <span>Approve & Resolve</span>
                  </Button>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
